"""Test cases for plugin output."""

import respx
from azul_runner import FV, Event, JobResult, State, test_template

from azul_plugin_nsrl.main import AzulPluginNsrl


class TestExecute(test_template.TestPlugin):
    PLUGIN_TO_TEST = AzulPluginNsrl

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.host = "localhost"
        cls.port = 8080

    def test_small_hit(self):
        """Validate when a small hit occurs the data is reasonable."""
        config = {"uri": f"http://{self.host}:{self.port}", "details": "True"}
        sha256 = "C5E167C0D08F05B44180E12194BA6471B195FB039CCBF4E0FE981BDEE97F080D"
        json_resonse = self.load_local_raw(
            "small_hit.json", description="Mock response data for an nsrl hit."
        ).decode()
        with respx.mock:
            respx.get(f"{config['uri']}/details/{sha256}").respond(text=json_resonse)
            result = self.do_execution(
                ent_id=sha256,
                config=config,
                no_multiprocessing=True,
            )
            self.assertJobResult(
                result,
                JobResult(
                    state=State(State.Label.COMPLETED),
                    events=[
                        Event(
                            entity_type="binary",
                            entity_id="C5E167C0D08F05B44180E12194BA6471B195FB039CCBF4E0FE981BDEE97F080D",
                            features={
                                "application": [
                                    FV(
                                        "SQL Server 2012 Standard Edition with Service Pack 2",
                                        label="Database Management System",
                                    ),
                                    FV("Sage 50 Accounting U.S. Edition", label="Accounting"),
                                ],
                                "application_versions": [
                                    FV("SQL Server 2012 Standard Edition with Service Pack 2", label="2014"),
                                    FV("Sage 50 Accounting U.S. Edition", label="2015"),
                                ],
                                "nsrl_hits": [FV(2)],
                                "nsrl_package_hits": [FV(2)],
                                "tag": [FV("NSRL")],
                            },
                        )
                    ],
                ),
            )

    def test_large_hit(self):
        """Validate when a huge amount of data is returned nothing too significant happens."""
        config = {"uri": f"http://{self.host}:{self.port}", "details": "True"}
        sha256 = "368F9CB089D206A8B61251F0C85EEDA97EE08A56B33BE8579246E964D3AF6169"
        json_resonse = self.load_local_raw("larg_hit.json", description="Mock response data for an nsrl hit.").decode()

        with respx.mock:
            respx.get(f"{config['uri']}/details/{sha256}").respond(text=json_resonse)
            result = self.do_execution(
                ent_id=sha256,
                config=config,
                no_multiprocessing=True,
            )
            self.assertJobResult(
                result,
                JobResult(
                    state=State(State.Label.COMPLETED),
                    events=[
                        Event(
                            entity_type="binary",
                            entity_id="368F9CB089D206A8B61251F0C85EEDA97EE08A56B33BE8579246E964D3AF6169",
                            features={
                                "application": [
                                    FV("Aomei Partition Assistant", label="Partition"),
                                    FV("Artweaver IrfanView AWD Plugin", label="plug-in"),
                                    FV("Capsa Enterprise", label="network monitoring"),
                                    FV("Corel PaintShop Pro", label="Graphic/Drawing"),
                                    FV("Epson WorkForce DS-780N", label="Scanner related"),
                                    FV("Glarysoft Utilities 5", label="Data wiping"),
                                    FV("Knight Online", label="Game"),
                                    FV("Realtek High Definition Audio Driver", label="Drivers"),
                                    FV("Website - www.down10.software", label="software collection"),
                                    FV("Windows Embedded Standard 2009", label="Operating System"),
                                ],
                                "application_versions": [
                                    FV("Aomei Partition Assistant", label="dl. 2022-06-16"),
                                    FV("Artweaver IrfanView AWD Plugin", label="4.57"),
                                    FV("Capsa Enterprise", label="12.0"),
                                    FV("Corel PaintShop Pro", label="2021"),
                                    FV("Epson WorkForce DS-780N", label="08/10/18,6.4.63.0"),
                                    FV("Glarysoft Utilities 5", label="5.190"),
                                    FV(
                                        "Knight Online",
                                        label=",1781103,1783900,1811295,1872128,1888450,1891248,1921083,3287885",
                                    ),
                                    FV("Realtek High Definition Audio Driver", label="6.0.1.7908,A06,Aug. 02, 2016"),
                                    FV("Website - www.down10.software", label="2022-09-21"),
                                    FV("Windows Embedded Standard 2009", label="2020-08-10"),
                                ],
                                "nsrl_hits": [FV(4954)],
                                "nsrl_package_hits": [FV(1136)],
                                "tag": [FV("NSRL")],
                            },
                        )
                    ],
                ),
            )

    def test_large_hit_less_max(self):
        """Validate when a huge amount of data is returned nothing too significant happens."""
        config = {"uri": f"http://{self.host}:{self.port}", "details": "True", "max_details": "2"}
        sha256 = "368F9CB089D206A8B61251F0C85EEDA97EE08A56B33BE8579246E964D3AF6169"
        json_resonse = self.load_local_raw("larg_hit.json", description="Mock response data for an nsrl hit.").decode()

        with respx.mock:
            respx.get(f"{config['uri']}/details/{sha256}").respond(text=json_resonse)
            result = self.do_execution(
                ent_id=sha256,
                config=config,
                no_multiprocessing=True,
            )
            self.assertJobResult(
                result,
                JobResult(
                    state=State(State.Label.COMPLETED),
                    events=[
                        Event(
                            entity_type="binary",
                            entity_id="368F9CB089D206A8B61251F0C85EEDA97EE08A56B33BE8579246E964D3AF6169",
                            features={
                                "application": [
                                    FV("Epson WorkForce DS-780N", label="Scanner related"),
                                    FV("Realtek High Definition Audio Driver", label="Drivers"),
                                ],
                                "application_versions": [
                                    FV("Epson WorkForce DS-780N", label="08/10/18,6.4.63.0"),
                                    FV("Realtek High Definition Audio Driver", label="6.0.1.7908,A06,Aug. 02, 2016"),
                                ],
                                "nsrl_hits": [FV(4954)],
                                "nsrl_package_hits": [FV(1136)],
                                "tag": [FV("NSRL")],
                            },
                        )
                    ],
                ),
            )
