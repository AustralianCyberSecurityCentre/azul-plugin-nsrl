"""Query the NSRL database to determine if a file is publicly known."""

from dataclasses import dataclass

import httpx
from azul_bedrock import models_network as azm
from azul_runner import (
    FV,
    Feature,
    FeatureType,
    Job,
    Plugin,
    State,
    add_settings,
    cmdline_run,
)
from nsrl_lookup_server.schema import FileDetails


@dataclass
class MinimalPackageDetails:
    """A minimal copy of package details data for temporary storage before being made into featureValues."""

    name: str = ""
    versions: set[str] = set
    app_type: str = ""


class AzulPluginNsrl(Plugin):
    """Query the NSRL database to determine if a file is publicly known."""

    VERSION = "2024.07.08"
    SETTINGS = add_settings(
        uri=(str, "http://nsrl-lookup-server"),
        details=(bool, False),
        max_details=(int, 10),
        # only process for new binary content
        filter_allow_event_types=[azm.BinaryAction.Extracted, azm.BinaryAction.Sourced],
    )
    FEATURES = [
        Feature(
            "nsrl_hits", desc="Number of packages with this hash found in the NSRL database.", type=FeatureType.Integer
        ),
        Feature(
            "nsrl_package_hits",
            desc="Number of packages (ignoring version) with this hash found in the NSRL database.",
            type=FeatureType.Integer,
        ),
        Feature(
            "application",
            desc="Name and type of the application from NSRL. (sample of total applications)",
            type=FeatureType.String,
        ),
        Feature(
            "application_versions",
            desc="Name and versions of the application from NSRL. (sample of total applications)",
            type=FeatureType.String,
        ),
        Feature("tag", desc="Any informational label about the sample", type=FeatureType.String),
    ]
    ENTITY_TYPE = "binary"

    def execute(self, job: Job):
        """Run the plugin."""
        # lookup based on digest priority order
        digest = job.event.entity.sha256

        action = "exists"
        if self.cfg.details is True:
            action = "details"
        url = f"{self.cfg.uri}/{action}/{digest}"
        try:
            r = httpx.get(url, follow_redirects=True, timeout=30.0)
        except httpx.TransportError as e:
            self.logger.error(
                f"Error looking up '{url}' with exception type {e.__class__.__name__} and content: "
                + f"{e.request.content.decode('utf-8')}"
            )
            raise
        if r.status_code == 200:
            self.add_feature_values("tag", "NSRL")
            if self.cfg.details is False:
                return
        elif r.status_code == 404:
            return
        else:
            return State(
                State.Label.ERROR_EXCEPTION, "Lookup Error", f"Error looking up digest: {r.status_code}: {r.text}"
            )

        packages: dict[str, MinimalPackageDetails] = dict()
        response_json = r.json()
        self.add_feature_values("nsrl_hits", len(response_json))
        for result in response_json:
            details = FileDetails(**result)
            package = details.package
            # If the package name or application type isn't set we aren't interested.
            if not package.name or not package.application_type:
                continue

            if package.name in packages:
                packages[package.name].versions.add(package.version)
            else:
                packages[package.name] = MinimalPackageDetails(
                    name=package.name.strip(),
                    versions=set([package.version.strip()]),
                    app_type=package.application_type.strip(),
                )

        self.add_feature_values("nsrl_package_hits", len(packages))

        if str(self.cfg.max_details).isdigit():
            max_details = int(self.cfg.max_details)
        else:
            raise Exception(f"Configuration exception {max_details} must be an integer value.")

        pkg_features = {}
        seen_app_types = set()
        skipped_pkgs = []
        for pkg in packages.values():
            if len(pkg_features.get("application", [])) >= max_details:
                break
            if pkg.app_type in seen_app_types:
                skipped_pkgs.append(pkg)
                continue

            pkg_features.setdefault("application", []).append(FV(pkg.name, label=pkg.app_type))
            pkg_features.setdefault("application_versions", []).append(
                FV(pkg.name, label=",".join(sorted(pkg.versions))[: self.cfg.max_value_length - 1])
            )
            seen_app_types.add(pkg.app_type)

        # If too many packages were skipped add them until we reach the max allowed.
        if len(pkg_features) < max_details and len(skipped_pkgs) > 0:
            for pkg in skipped_pkgs:
                if len(pkg_features.get("application", [])) >= max_details:
                    break

                pkg_features.setdefault("application", []).append(FV(pkg.name, label=pkg.app_type))
                pkg_features.setdefault("application_versions", []).append(
                    FV(pkg.name, label=",".join(pkg.versions)[: self.cfg.max_value_length - 1])
                )

        self.add_many_feature_values(pkg_features)


def main():
    """Plugin command-line entrypoint."""
    cmdline_run(plugin=AzulPluginNsrl)


if __name__ == "__main__":
    main()
