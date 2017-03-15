# To run this test you'll need to download geckodriver to
# /usr/local/bin/ or any other place in user $PATH.
# Download from https://github.com/mozilla/geckodriver/releases

from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver

from valuenetwork.valueaccounting.models import AgentType, EconomicAgent

class WorkAppTestCase(LiveServerTestCase):
    def setUp(self):
        User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@example.com'
        )
        project_agent_type = AgentType.objects.create(
            name='Project',
            party_type='team',
            is_context=True
        )
        EconomicAgent.objects.create(
            name='Membership Requests',
            nick='FC MembershipRequest',
            agent_type=project_agent_type,
            is_context=True
        )
        self.selenium = webdriver.Firefox()
        self.selenium.maximize_window()
        super(WorkAppTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(AdminTestCase, self).tearDown()

    def test_membership_request(self):
        s = self.selenium

        # User fills the membership request form.
        s.get('%s%s' % (self.live_server_url, "/"))
        assert "OCP: Open Collaborative Platform" in s.title
        s.find_element_by_link_text("Join FreedomCoop")
        s.get('%s%s' % (self.live_server_url, "/membership/"))
        self.assertIn("Request Membership at FreedomCoop", s.title)
        s.find_element_by_id("id_name").send_keys("testuser01")
        s.find_element_by_id("id_requested_username").send_keys("testuser01")
        s.find_element_by_id("id_email_address").send_keys("testuser01@example.com")
        s.find_element_by_id("id_description").send_keys("This is a test user.")
        s.find_element_by_xpath('//input[@value="Submit"]').click()
        assert "Thank you for your membership request" in s.title

        # Admin login.
        s.get('%s%s' % (self.live_server_url, "/"))
        assert "OCP: Open Collaborative Platform" in s.title
        s.find_element_by_id("id_username").send_keys("admin")
        s.find_element_by_id("id_password").send_keys("admin")
        s.find_element_by_xpath('//input[@value="Log in"]').click()

        # Admin takes the simple task (accounting/work -> Mine!)

        # Admin creates agent (click url -> click Create Agent)

        # Admin creates user (click Create user -> enter new password)

        # Admin defines associations (click Maintain Associations)
        # - change "is participant of" -> FC membership
        # - change "Active" -> candidate (or member?)