from bot import parse_command
import unittest


class BotTestCase(unittest.TestCase):

    def test_should_return_one_service_to_deploy(self):
        command = "deploy to prod service1:tag1"
        cmd, cluster, services = parse_command(command)

        self.assertEqual(cmd, "deploy")
        self.assertEqual(cluster, "prod")
        self.assertEqual(services[0]["service"], "service1")
        self.assertEqual(services[0]["tag"], "tag1")

    def test_should_return_three_services_to_deploy(self):
        command = "deploy to prod service1:tag1,service2:tag2,service3:tag3"
        cmd, cluster, services = parse_command(command)

        self.assertEqual(len(services), 3)
        self.assertEqual(services[0]["service"], "service1")
        self.assertEqual(services[0]["tag"], "tag1")
        self.assertEqual(services[2]["service"], "service3")
        self.assertEqual(services[2]["tag"], "tag3")

    def test_should_return_service1_with_tag_null(self):
        command = "deploy to prod service1"
        cmd, cluster, services = parse_command(command)

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service"], "service1")
        self.assertEqual(services[0]["tag"], None)

    def test_should_raise_error_for_no_match(self):
        command = "deploy to prod"
        self.assertRaises(ValueError, lambda: parse_command(command))

    def test_should_deploy_all(self):
        command = "deploy to prod all:tag"
        cmd, cluster, services = parse_command(command)

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service"], "all")
        self.assertEqual(services[0]["tag"], "tag")
