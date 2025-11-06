"""Test cases for plugin output."""

import os
import sqlite3
import tempfile
import time
from multiprocessing import Process

from azul_runner import FV, Event, JobResult, State, test_template

from azul_plugin_nsrl.main import AzulPluginNsrl


class TestExecute(test_template.TestPlugin):
    PLUGIN_TO_TEST = AzulPluginNsrl

    @classmethod
    def setUpClass(cls) -> None:
        """Construct a test database."""
        super().setUpClass()
        cls.db_file = tempfile.NamedTemporaryFile(prefix="dontletrunnerdelete").name

        db = sqlite3.connect(cls.db_file)
        script = os.path.join(os.path.dirname(__file__), "data", "rdsv3_minimal.schema.sql")
        with open(script) as f:
            db.executescript(f.read())

        cls.valid_sha256 = "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
        cls.valid_sha1 = "AC91EF00F33F12DD491CC91EF00F33F12DD491CA"
        cls.valid_md5 = "DC2311FFDC0015FCCC12130FF145DE78"
        cls.partial_sha256a = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E541"
        cls.partial_sha256b = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E542"
        cls.partial_sha256c = "50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E543"
        cls.partial_sha1a = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932131"
        cls.partial_sha1b = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932132"
        cls.partial_sha1c = "6A3AD39E5EAC4B7A4D2DC7DCBB6E40A204932133"
        cls.partial_md5a = "1B6A3B720DEC5E60FDA2ECB0EE713661"
        cls.partial_md5b = "1B6A3B720DEC5E60FDA2ECB0EE713662"
        cls.partial_md5c = "1B6A3B720DEC5E60FDA2ECB0EE713663"
        script = f"""
            insert into MFG values ('1', 'Microsoft Corporation');
            insert into MFG values ('2', 'Rand Corporation');
            insert into OS values ('1', 'Windows NT', '4.0', '1');
            insert into OS values ('2', 'Custom OS', '1.0', '2');
            insert into PKG values ('1', 'Microsoft Word', '2000', '1', '1', 'English', 'Operating System');
            insert into PKG values ('2', 'Word', '2000', '1', '1', 'English', 'Operating System');
            insert into PKG values ('3', 'PKG1', '2007', '2', '2', 'English', 'Operating System');
            insert into PKG values ('4', 'PKG1', '2007', NULL, '2', 'English', 'Operating System');
            insert into PKG values ('5', 'PKG1', '2007', '2', NULL, 'English', 'Operating System');
            insert into FILE values ('{cls.valid_sha256}', '{cls.valid_sha1}', '{cls.valid_md5}', 'WORD.EXE', '1217645', '1');
            insert into FILE values ('{cls.valid_sha256}', '{cls.valid_sha1}', '{cls.valid_md5}', 'WORD.EXE', '1217645', '2');
            insert into FILE values ('{cls.partial_sha256a}', '{cls.partial_sha1a}', '{cls.partial_md5a}', 'FILEa.EXE', '123456', '3');
            insert into FILE values ('{cls.partial_sha256b}', '{cls.partial_sha1b}', '{cls.partial_md5b}', 'FILEb.EXE', '123456', '4');
            insert into FILE values ('{cls.partial_sha256c}', '{cls.partial_sha1c}', '{cls.partial_md5c}', 'FILEc.EXE', '123456', '5');
        """

        db.executescript(script)
        db.commit()
        db.close()

        cls.host = "localhost"
        cls.port = 8080
        os.environ["NSRL_DB_FILEPATH"] = cls.db_file
        os.environ["NSRL_SERVER_HOST"] = cls.host
        os.environ["NSRL_SERVER_PORT"] = str(cls.port)
        # delay import until after env is set, so correct config is applied
        from nsrl_lookup_server import cli

        cls.server = Process(
            target=cli.server,
            daemon=True,
        )
        cls.server.start()
        time.sleep(1.5)  # wait for server to start

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove the test database."""
        super().tearDownClass()
        try:
            cls.server.terminate()
        except:
            pass
        try:
            os.unlink(cls.db_file)
        except:
            pass

    def test_exists(self):
        """Test a "exists" lookup"""
        config = {"uri": f"http://{self.host}:{self.port}"}
        # test valid sha256
        result = self.do_execution(
            ent_id=self.valid_sha256,
            config=config,
        )

        self.assertJobResult(
            result,
            JobResult(
                state=State(State.Label.COMPLETED),
                events=[
                    Event(
                        entity_type="binary",
                        entity_id=self.valid_sha256,
                        features={
                            "tag": [FV("NSRL")],
                        },
                    )
                ],
            ),
        )

    def test_dne_exists(self):
        """Test a "exists" lookup where the hash is not there"""
        # test valid sha256
        result = self.do_execution(
            ent_id="A" * 64,
            config={"uri": f"http://{self.host}:{self.port}"},
        )

        self.assertJobResult(
            result,
            JobResult(state=State(State.Label.COMPLETED_EMPTY)),
        )

    def test_details(self):
        """Test a "details" lookup"""
        config = {
            "uri": f"http://{self.host}:{self.port}",
            "details": "True",
        }
        # test valid sha256
        result = self.do_execution(
            ent_id=self.valid_sha256,
            config=config,
        )

        self.assertJobResult(
            result,
            JobResult(
                state=State(State.Label.COMPLETED),
                events=[
                    Event(
                        entity_type="binary",
                        entity_id="E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                        features={
                            "application": [
                                FV("Microsoft Word", label="Operating System"),
                                FV("Word", label="Operating System"),
                            ],
                            "application_versions": [FV("Microsoft Word", label="2000"), FV("Word", label="2000")],
                            "nsrl_hits": [FV(2)],
                            "nsrl_package_hits": [FV(2)],
                            "tag": [FV("NSRL")],
                        },
                    )
                ],
            ),
        )

    def test_dne_details(self):
        """Test a "details" lookup where the hash is not there"""
        # test valid sha256
        result = self.do_execution(
            ent_id="A" * 64,
            config={
                "uri": f"http://{self.host}:{self.port}",
                "details": "True",
            },
        )

        self.assertJobResult(
            result,
            JobResult(state=State(State.Label.COMPLETED_EMPTY)),
        )

    def test_partial_details(self):
        """Validate full lookup on partial data."""
        result = self.do_execution(
            ent_id=self.partial_sha256a,
            config={
                "uri": f"http://{self.host}:{self.port}",
                "details": "True",
            },
        )

        self.assertJobResult(
            result,
            JobResult(
                state=State(State.Label.COMPLETED),
                events=[
                    Event(
                        entity_type="binary",
                        entity_id="50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E541",
                        features={
                            "application": [FV("PKG1", label="Operating System")],
                            "application_versions": [FV("PKG1", label="2007")],
                            "nsrl_hits": [FV(1)],
                            "nsrl_package_hits": [FV(1)],
                            "tag": [FV("NSRL")],
                        },
                    )
                ],
            ),
        )

    def test_partial_details_missing_os(self):
        """Validate partial details lookups with operating system info missing."""
        result = self.do_execution(
            ent_id=self.partial_sha256b,
            config={
                "uri": f"http://{self.host}:{self.port}",
                "details": "True",
            },
        )

        self.assertJobResult(
            result,
            JobResult(
                state=State(State.Label.COMPLETED),
                events=[
                    Event(
                        entity_type="binary",
                        entity_id="50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E542",
                        features={
                            "application": [FV("PKG1", label="Operating System")],
                            "application_versions": [FV("PKG1", label="2007")],
                            "nsrl_hits": [FV(1)],
                            "nsrl_package_hits": [FV(1)],
                            "tag": [FV("NSRL")],
                        },
                    )
                ],
            ),
        )

    def test_partial_details_missing_manufacturer(self):
        """Validate partial details lookups with manufacturer info missing."""
        result = self.do_execution(
            ent_id=self.partial_sha256c,
            config={
                "uri": f"http://{self.host}:{self.port}",
                "details": "True",
            },
        )

        self.assertJobResult(
            result,
            JobResult(
                state=State(State.Label.COMPLETED),
                events=[
                    Event(
                        entity_type="binary",
                        entity_id="50B2C6C05BBDEF754ABA71FFB1A88A03A48D63CA7426049435A568093825E543",
                        features={
                            "application": [FV("PKG1", label="Operating System")],
                            "application_versions": [FV("PKG1", label="2007")],
                            "nsrl_hits": [FV(1)],
                            "nsrl_package_hits": [FV(1)],
                            "tag": [FV("NSRL")],
                        },
                    )
                ],
            ),
        )
