# To run this test you'll need to download geckodriver to
# /usr/local/bin/ or any other place in user $PATH.
# Download from https://github.com/mozilla/geckodriver/releases

from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from django.conf import settings

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from valuenetwork.valueaccounting.models import AgentType, EconomicAgent, EventType, EconomicResourceType

class MembershipRequestTestCase(LiveServerTestCase):
    def setUp(self):
        # If you want to see debugging errors in the browser while making changes in the test,
        # uncomment this line and comment tearDown() method.
        #setattr(settings, 'DEBUG', True)

        # We want to reuse the test db, to be faster (manage.py test --keepdb).
        # So we create the objects only if they are not in test db.
        try:
            User.objects.get(username='admin')
        except User.DoesNotExist:
            User.objects.create_superuser(
                username='admin',
                password='admin',
                email='admin@example.com'
            )

        try:
            AgentType.objects.get(name='Project')
        except AgentType.DoesNotExist:
            project_agent_type = AgentType.objects.create(
                name='Project',
                party_type='team',
                is_context=True
            )

        try:
            EconomicAgent.objects.get(name='Membership Requests')
        except EconomicAgent.DoesNotExist:
            EconomicAgent.objects.create(
                name='Membership Requests',
                nick='FC MembershipRequest',
                agent_type=project_agent_type,
                is_context=True
            )

        try:
            EventType.objects.get(relationship='todo')
        except EventType.DoesNotExist:
            EventType.objects.create(
                name='Todo',
                label='todo',
                relationship='todo',
                related_to='agent',
                resource_effect='=',
            )

        try:
            EconomicResourceType.objects.get(behavior='work')
        except EconomicResourceType.DoesNotExist:
            EconomicResourceType.objects.create(
                name='something_with_Admin',
                behavior='work',
            )

        self.selenium = webdriver.Firefox()
        self.selenium.implicitly_wait(2)
        self.selenium.maximize_window()
        super(MembershipRequestTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(MembershipRequestTestCase, self).tearDown()

    def wait_for_load_new_page(self, driver, title):
        try:
            element = WebDriverWait(driver, 10).until(EC.title_contains(title))
            return True
        except TimeoutException as ex:
            print("Exception has been thrown. " + str(ex))
            self.tearDown()

    def test_membership_request(self):
        s = self.selenium

        # User fills the membership request form.
        s.get('%s%s' % (self.live_server_url, "/"))
        self.wait_for_load_new_page(s, "OCP: Open Collaborative Platform")
        s.find_element_by_link_text("Join FreedomCoop").click()
        self.wait_for_load_new_page(s, "Request Membership at FreedomCoop")
        s.find_element_by_id("id_name").send_keys("testuser01")
        s.find_element_by_id("id_requested_username").send_keys("testuser01")
        s.find_element_by_id("id_email_address").send_keys("testuser01@example.com")
        s.find_element_by_id("id_description").send_keys("This is a test user.")
        s.find_element_by_xpath('//input[@value="Submit"]').click()
        self.wait_for_load_new_page(s, "Thank you for your membership request")

        # Admin login.
        s.get('%s%s' % (self.live_server_url, "/"))
        self.wait_for_load_new_page(s, "OCP: Open Collaborative Platform")
        s.find_element_by_id("id_username").send_keys("admin")
        s.find_element_by_id("id_password").send_keys("admin")
        s.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_for_load_new_page(s, "My Dashboard")

        # Admin takes the simple task (accounting/work -> Mine!)

        # Admin creates agent (click url -> click Create Agent)

        # Admin creates user (click Create user -> enter new password)

        # Admin defines associations (click Maintain Associations)
        # - change "is participant of" -> FC membership
        # - change "Active" -> candidate (or member?)
