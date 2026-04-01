"""
Seed 60 realistic NovaCRM support tickets + 15 KB articles.
All tickets are pre-classified so the demo works without an API key.
"""

from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
import db


def _ago(days: float, hours: float = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days, hours=hours)
    return dt.isoformat()


def init() -> None:
    if db.get_all_tickets():
        return
    random.seed(7)
    _seed_kb()
    _seed_tickets()


# ── KB Articles ───────────────────────────────────────────────────────────────

def _seed_kb() -> None:
    articles = [
        # Billing
        ("How to download your invoice", "Billing",
         "billing invoice download receipt",
         "To download your invoice: go to Settings → Billing → Invoice History. "
         "Click the download icon next to any invoice. Invoices are available in PDF format. "
         "For invoices older than 12 months, contact billing@novacrm.com."),
        ("How to upgrade or downgrade your plan", "Billing",
         "upgrade downgrade plan subscription change",
         "To change your plan: Settings → Billing → Change Plan. Select your new plan and confirm. "
         "Upgrades take effect immediately and are prorated. Downgrades take effect at next billing cycle. "
         "Annual plans can only be changed at renewal."),
        ("Why was I charged unexpectedly", "Billing",
         "unexpected charge payment billing question",
         "Common reasons for unexpected charges: (1) seat overage — you exceeded your plan's seat limit, "
         "(2) annual renewal — your subscription renewed automatically, "
         "(3) feature add-on activated. Check Settings → Billing → Usage for a breakdown."),

        # Bug Report
        ("Login issues and password reset", "Bug Report",
         "login password reset locked out 2fa",
         "If you can't log in: (1) Use 'Forgot Password' on the login page. "
         "(2) Check your email for a reset link — check spam. (3) If you have 2FA enabled, "
         "use a backup code from Settings → Security → 2FA Backup Codes. "
         "If still locked out, contact your account admin."),
        ("Data not syncing between NovaCRM and connected apps", "Bug Report",
         "sync data not updating refresh integration",
         "If data isn't syncing: (1) Go to Settings → Integrations and reconnect the affected integration. "
         "(2) Check that your API credentials haven't expired. (3) Click 'Force Sync' in the integration settings. "
         "Syncs run every 15 minutes by default; manual sync runs immediately."),
        ("Export feature not working", "Bug Report",
         "export csv download data not working broken",
         "If exports fail: (1) Try a smaller date range — exports over 100k rows may time out. "
         "(2) Use Chrome or Firefox — Safari has known issues with large file downloads. "
         "(3) Check that your role has export permissions (Settings → Team → Roles). "
         "If the issue persists, contact support with your export settings."),

        # Integration
        ("Setting up Salesforce integration", "Integration",
         "salesforce setup connect integration crm",
         "To connect Salesforce: (1) Settings → Integrations → Salesforce → Connect. "
         "(2) Authorize with your Salesforce admin credentials. (3) Map your fields in the field mapping screen. "
         "(4) Select sync direction: one-way or bidirectional. Full sync runs on first connect (~30 mins for large orgs)."),
        ("Slack notifications not sending", "Integration",
         "slack notifications alerts not working",
         "To fix Slack notifications: (1) Settings → Integrations → Slack → Reconnect. "
         "(2) Ensure the NovaCRM Slack app has permission to post to your channel. "
         "(3) Check your notification preferences — notifications may be disabled for your event type. "
         "Test with the 'Send test notification' button."),
        ("Setting up API webhooks", "Integration",
         "api webhook endpoint developer integration",
         "To set up webhooks: Settings → Developer → Webhooks → Add Endpoint. "
         "Provide your HTTPS endpoint URL and select events to subscribe to. "
         "We'll send a verification request — respond with the challenge value. "
         "See docs.novacrm.com/api/webhooks for full documentation and payload schemas."),

        # Onboarding
        ("Getting started with NovaCRM", "Onboarding",
         "getting started setup guide new user onboarding",
         "Welcome to NovaCRM! Start here: (1) Complete your profile in Settings → Profile. "
         "(2) Import your contacts via Settings → Import → CSV. "
         "(3) Connect your email in Settings → Email → Connect. "
         "(4) Invite your team in Settings → Team → Invite. "
         "Your onboarding checklist is in the dashboard top bar."),
        ("How to configure SSO", "Onboarding",
         "sso single sign on saml okta azure ad login",
         "To configure SSO: Settings → Security → SSO. We support SAML 2.0 (Okta, Azure AD, Google Workspace). "
         "Enter your IdP metadata URL or upload the XML file. "
         "Test with one user before enforcing SSO for all users. "
         "See docs.novacrm.com/security/sso for IdP-specific guides."),
        ("How to invite team members", "Onboarding",
         "invite team user add member seat",
         "To invite team members: Settings → Team → Invite Members. "
         "Enter email addresses (comma-separated for bulk). Assign a role: Admin, Manager, or User. "
         "Invites expire after 7 days — resend from the Pending Invites tab. "
         "Seats are added automatically and billed at your current per-seat rate."),

        # Account
        ("How to reset your password", "Account",
         "password reset forgot locked account",
         "To reset your password: (1) Click 'Forgot Password' on the login page. "
         "(2) Enter your account email — check spam for the reset email. "
         "(3) Link expires in 1 hour. If it expired, request a new one. "
         "If you're locked out after too many attempts, wait 30 minutes or contact your admin."),
        ("Managing seat limits and user access", "Account",
         "seat limit user access role permissions",
         "Seat limits are defined by your plan. To view: Settings → Billing → Current Plan. "
         "To remove a user and free a seat: Settings → Team → select user → Deactivate. "
         "Deactivated users lose access immediately but their data is retained. "
         "To add seats: Settings → Billing → Add Seats (billed prorated)."),
        ("Two-factor authentication setup and issues", "Account",
         "2fa two factor authentication security code",
         "To enable 2FA: Settings → Security → Two-Factor Authentication → Enable. "
         "Use an authenticator app (Google Authenticator, Authy). Save your backup codes. "
         "If you lose access to your 2FA device, use a backup code from your saved list, "
         "or ask your account admin to disable 2FA for your account temporarily."),
    ]
    for title, category, tags, content in articles:
        db.create_kb_article(title, content, category, tags)


# ── Tickets ───────────────────────────────────────────────────────────────────

def _seed_tickets() -> None:
    agents = ["sarah@novacrm.com", "james@novacrm.com", "priya@novacrm.com", None]

    tickets = [
        # ── BILLING (15) ─────────────────────────────────────────────────────
        ("Charged twice for last month", "Billing", "P1", "ANGRY", "OPEN", None,
         "sarah.chen@acmecorp.com", "Sarah Chen",
         "I was charged $299 twice on my credit card on October 1st. "
         "This is unacceptable. I need an immediate refund for the duplicate charge. "
         "Order #INV-2024-10-0045.",
         "Customer reports duplicate charge of $299. Needs refund and investigation.", 0.91),

        ("Can't find my invoice", "Billing", "P3", "NEUTRAL", "DEFLECTED", None,
         "mark.johnson@techstart.io", "Mark Johnson",
         "Hi, I need to download my invoice from September for my accounting team. "
         "I can't find where to access past invoices in the settings.",
         "Customer can't locate invoice download feature in Settings.", 0.95),

        ("Want to upgrade from Starter to Business plan", "Billing", "P2", "SATISFIED", "RESOLVED",
         "james@novacrm.com",
         "lisa.wong@globalfirm.com", "Lisa Wong",
         "We've grown from 5 to 20 users and need to upgrade our plan. "
         "Can you help me understand the pricing and what's included in Business?",
         "Customer wants to upgrade plan — 5 to 20 seats, needs pricing info.", 0.87),

        ("Annual renewal charge I wasn't expecting", "Billing", "P2", "FRUSTRATED", "IN_PROGRESS",
         "priya@novacrm.com",
         "tom.harris@retailco.com", "Tom Harris",
         "I was charged $2,400 today and I didn't expect it. "
         "I thought I had cancelled or was on monthly billing. Please help.",
         "Unexpected annual renewal charge — customer may have missed renewal notification.", 0.83),

        ("Need to downgrade our plan due to budget cuts", "Billing", "P2", "NEUTRAL", "OPEN", None,
         "anna.kim@nonprofit.org", "Anna Kim",
         "Due to budget constraints, we need to move from Business to Starter. "
         "We have 8 seats currently. Will we lose any data? When does it take effect?",
         "Customer needs to downgrade plan — concerned about data retention.", 0.88),

        ("Seat overage charge explanation", "Billing", "P2", "FRUSTRATED", "RESOLVED",
         "sarah@novacrm.com",
         "carlos.ruiz@agency.net", "Carlos Ruiz",
         "We got charged an extra $150 that we don't understand. "
         "We're on the Starter plan with 10 seats — did we go over?",
         "Seat overage charge on Starter plan — customer needs explanation.", 0.79),

        ("Invoice shows wrong company name", "Billing", "P2", "NEUTRAL", "OPEN", None,
         "jen.li@consulting.com", "Jennifer Li",
         "Our last three invoices show our old company name 'Li Consulting LLC' "
         "but we rebranded to 'Nexus Advisory Group'. Can this be corrected?",
         "Customer needs billing name updated to new company name.", 0.82),

        ("Failed payment — credit card expired", "Billing", "P1", "FRUSTRATED", "OPEN", None,
         "raj.patel@startupxyz.com", "Raj Patel",
         "I keep getting payment failed emails. I updated my card but it's still showing the old one. "
         "My account says it will be suspended in 3 days. Please help urgently.",
         "Payment failure after card update — account at risk of suspension.", 0.90),

        ("Refund request for unused months", "Billing", "P2", "NEUTRAL", "ESCALATED",
         "james@novacrm.com",
         "beth.moore@enterprise.co", "Beth Moore",
         "We signed up for annual but have barely used the product. "
         "We're 3 months in — can we get a prorated refund for the remaining 9 months?",
         "Customer requesting prorated refund for annual plan — escalated to billing team.", 0.75),

        ("Need VAT invoice for EU compliance", "Billing", "P3", "NEUTRAL", "RESOLVED",
         "sarah@novacrm.com",
         "pieter.van@eurobiz.nl", "Pieter van der Berg",
         "We're based in the Netherlands and need VAT-compliant invoices. "
         "Our current invoices don't show our VAT number or the correct tax breakdown.",
         "EU customer needs VAT-compliant invoices with tax number.", 0.85),

        ("Can I pay annually with a purchase order", "Billing", "P3", "NEUTRAL", "OPEN", None,
         "procurement@bigcorp.com", "BigCorp Procurement",
         "Our company policy requires purchase orders for annual software subscriptions over $5,000. "
         "Is this payment method supported? We're looking at the Enterprise plan.",
         "Enterprise prospect asking about purchase order payment method.", 0.80),

        ("Discount request for nonprofit status", "Billing", "P3", "NEUTRAL", "OPEN", None,
         "director@charityhq.org", "Amanda Foster",
         "We're a registered 501(c)(3) nonprofit. Do you offer discounts for nonprofit organizations? "
         "We're currently comparing several CRM options.",
         "Nonprofit organization requesting discount pricing.", 0.77),

        ("Transaction declined but still charged", "Billing", "P0", "ANGRY", "OPEN", None,
         "finance@urgentco.com", "David Park",
         "This is urgent. Our payment was declined according to our bank, but NovaCRM shows "
         "the payment as successful and our account is active. We may have been charged without consent. "
         "Need immediate investigation.",
         "P0: Potential unauthorized charge — payment shows declined on bank but active in system.", 0.94),

        ("How do I add a backup payment method", "Billing", "P3", "NEUTRAL", "DEFLECTED", None,
         "ops@techteam.io", "Chris Banks",
         "We want to add a secondary credit card as backup in case our primary card fails. "
         "Is this possible in the billing settings?",
         "Customer wants to add backup payment method.", 0.92),

        ("Invoice currency changed without notice", "Billing", "P1", "FRUSTRATED", "OPEN", None,
         "admin@globalops.sg", "Helen Tan",
         "Our invoices suddenly switched from USD to SGD pricing. We didn't request this change. "
         "The SGD rate seems higher than what we were paying. Please revert to USD billing.",
         "Invoice currency changed unexpectedly from USD to SGD.", 0.86),

        # ── BUG REPORTS (15) ──────────────────────────────────────────────────
        ("Can't log in — getting 'invalid credentials' error", "Bug Report", "P1", "FRUSTRATED", "OPEN", None,
         "ceo@smallbiz.com", "Michael Torres",
         "I've been trying to log in for 2 hours. I know my password is correct because I just reset it. "
         "Keep getting 'invalid credentials'. This is blocking my whole team.",
         "Login failure after password reset — blocking the entire team.", 0.92),

        ("Data not showing after import", "Bug Report", "P1", "FRUSTRATED", "IN_PROGRESS",
         "sarah@novacrm.com",
         "operations@company.com", "Sam Richardson",
         "We imported 5,000 contacts yesterday. The import said it was successful but "
         "we can only see 847 contacts in our database. Where did the rest go?",
         "Partial import — 4,153 contacts missing after successful import notification.", 0.89),

        ("Export to CSV button does nothing", "Bug Report", "P2", "NEUTRAL", "OPEN", None,
         "analyst@dataco.com", "Patricia Wells",
         "When I click Export to CSV in the Contacts view, nothing happens. "
         "No download, no error message. Tried in Chrome and Firefox. "
         "This was working fine last week.",
         "CSV export button unresponsive — regression from last week.", 0.84),

        ("Dashboard not loading — infinite spinner", "Bug Report", "P0", "ANGRY", "ESCALATED",
         "james@novacrm.com",
         "cto@criticalapp.com", "James Wu",
         "Our entire team cannot access the NovaCRM dashboard. "
         "It's been showing an infinite loading spinner for 45 minutes. "
         "We have demos with clients today — this is a business emergency.",
         "P0: Full dashboard outage for entire team — client demos at risk.", 0.97),

        ("Email sequences not sending", "Bug Report", "P1", "FRUSTRATED", "OPEN", None,
         "marketing@growthco.com", "Rachel Green",
         "We set up an automated email sequence 3 days ago and it hasn't sent a single email. "
         "The sequence shows 'Active' status but 0 emails sent. "
         "We have 200+ contacts waiting in the sequence.",
         "Email automation sequence active but sending zero emails for 3 days.", 0.91),

        ("Contact merge losing data", "Bug Report", "P1", "ANGRY", "OPEN", None,
         "crm@salesteam.net", "Kevin Brown",
         "I merged two duplicate contacts and the resulting contact is missing the activity history "
         "from one of the original contacts. This is a data loss issue. "
         "Can the original data be recovered?",
         "Contact merge resulted in data loss — activity history missing.", 0.88),

        ("Reports module showing wrong date range", "Bug Report", "P2", "FRUSTRATED", "IN_PROGRESS",
         "priya@novacrm.com",
         "data@analytics.co", "Fiona Scott",
         "When I select 'Last 30 days' in the Reports module, it shows data from the last 60 days. "
         "The date filter appears to be off by exactly 30 days.",
         "Reports date filter bug — 'Last 30 days' showing 60 days of data.", 0.87),

        ("Mobile app crashing on iOS 17", "Bug Report", "P2", "FRUSTRATED", "OPEN", None,
         "field@salesrep.com", "Derek Mills",
         "The NovaCRM mobile app crashes immediately after login on iPhone 15 (iOS 17.1). "
         "It was fine before the iOS update. Other team members on older iOS versions are fine.",
         "iOS 17.1 crash on launch — regression after iOS update.", 0.90),

        ("API rate limit errors despite low usage", "Bug Report", "P2", "NEUTRAL", "OPEN", None,
         "dev@techsolutions.io", "Nina Patel",
         "We're getting 429 rate limit errors from the API but we're only making about 50 requests/hour. "
         "Our plan allows 1,000 requests/hour. Something seems wrong with the rate limit tracking.",
         "API rate limit errors at 50 req/hr despite 1000 req/hr plan limit.", 0.82),

        ("Search returning no results for existing records", "Bug Report", "P1", "FRUSTRATED", "OPEN", None,
         "support@clientx.com", "Oliver Harris",
         "The global search is broken. I search for contacts that I can see in the list view, "
         "but search returns 'No results found'. Started happening 2 days ago.",
         "Global search returning no results — records visible in list view but unsearchable.", 0.93),

        ("Custom fields not saving", "Bug Report", "P2", "NEUTRAL", "RESOLVED",
         "james@novacrm.com",
         "admin@retailbrand.com", "Sophie Clarke",
         "I created 5 custom fields for our pipeline. When I enter values and save, "
         "the values disappear when I refresh the page.",
         "Custom field values not persisting after save.", 0.85),

        ("Duplicate contacts being created by sync", "Bug Report", "P2", "FRUSTRATED", "IN_PROGRESS",
         "sarah@novacrm.com",
         "ops@consultingfirm.com", "Bruce Lee",
         "Since we connected our Mailchimp integration, it's creating duplicate contacts. "
         "We now have 3,000 duplicates. The sync seems to create a new contact instead of updating.",
         "Mailchimp sync creating duplicates instead of updating existing contacts.", 0.88),

        ("Notification emails going to spam", "Bug Report", "P2", "NEUTRAL", "OPEN", None,
         "it@manufacturing.com", "Tracy Edwards",
         "All NovaCRM notification emails (task reminders, deal updates) are landing in spam "
         "for our entire team. We've whitelisted the domain but it's still happening.",
         "Notification emails marked as spam — team-wide issue after domain whitelisting.", 0.80),

        ("Time zone bug in scheduled tasks", "Bug Report", "P2", "FRUSTRATED", "OPEN", None,
         "pm@remote.team", "Yuki Tanaka",
         "Tasks scheduled for 9am in our CRM are triggering at 2pm. "
         "I'm in Tokyo (JST) but the system seems to be using US Eastern time despite my settings.",
         "Timezone mismatch in task scheduling — JST vs EST offset issue.", 0.83),

        ("2FA codes not working", "Bug Report", "P1", "ANGRY", "OPEN", None,
         "admin@securecorp.com", "Greg Hoffman",
         "None of our team can use 2FA. The codes from our authenticator app are being rejected. "
         "We believe our account's TOTP secret may have been rotated without our knowledge. "
         "We're locked out of the account.",
         "2FA codes rejected for entire team — possible TOTP secret rotation.", 0.94),

        # ── INTEGRATIONS (10) ─────────────────────────────────────────────────
        ("Salesforce sync not bringing over custom fields", "Integration", "P2", "FRUSTRATED", "OPEN", None,
         "sfadmin@bigco.com", "Tanya Brooks",
         "We have 12 custom fields in Salesforce that we mapped in NovaCRM. "
         "Standard fields sync fine but custom fields show as blank. "
         "The field mapping screen shows them as mapped.",
         "Salesforce custom field mapping not syncing despite correct configuration.", 0.87),

        ("How do I connect Slack to NovaCRM", "Integration", "P3", "NEUTRAL", "DEFLECTED", None,
         "ops@startupteam.com", "Felix Rivera",
         "We just signed up and want to get Slack notifications when deals are won or tasks are due. "
         "Where do I set this up?",
         "New customer asking how to set up Slack integration.", 0.96),

        ("Zapier integration returning authentication error", "Integration", "P2", "FRUSTRATED", "OPEN", None,
         "automation@agency.com", "Donna Chase",
         "Our Zapier workflows keep failing with 'Authentication failed' errors. "
         "I regenerated my API key and updated it in Zapier but still failing.",
         "Zapier authentication failures after API key regeneration.", 0.84),

        ("Webhook not firing on deal close events", "Integration", "P2", "NEUTRAL", "IN_PROGRESS",
         "priya@novacrm.com",
         "backend@saasco.io", "Aaron Kim",
         "Our webhook endpoint should fire when a deal is marked as Won, "
         "but we're not receiving any events. We tested the endpoint — it's working fine.",
         "Webhook not triggering on deal.won events despite valid endpoint.", 0.86),

        ("Google Calendar sync creating duplicate events", "Integration", "P2", "FRUSTRATED", "OPEN", None,
         "sales@propertyco.com", "Monica Singh",
         "Since connecting Google Calendar, every meeting I create in NovaCRM "
         "appears twice in my Google Calendar. I've disconnected and reconnected twice.",
         "Google Calendar sync creating duplicate events — persistent after reconnect.", 0.88),

        ("HubSpot to NovaCRM migration — contacts not mapping", "Integration", "P1", "FRUSTRATED", "OPEN", None,
         "marketing@migratingco.com", "Paul Zhang",
         "We're migrating from HubSpot. We exported our 15,000 contacts and "
         "the import is mapping company names to the wrong field. "
         "All company names are ending up in the 'Notes' field.",
         "HubSpot migration field mapping error — company names going to Notes.", 0.81),

        ("Stripe integration not creating deals on payment", "Integration", "P2", "NEUTRAL", "OPEN", None,
         "finance@productco.com", "Laura Chen",
         "We set up the Stripe integration to auto-create deals when payments succeed. "
         "We've had 23 Stripe payments in the past week but 0 deals created in NovaCRM.",
         "Stripe payment webhook not creating deals — 23 missed events.", 0.85),

        ("LinkedIn Sales Navigator sync stopped working", "Integration", "P2", "FRUSTRATED", "OPEN", None,
         "sdr@salesteam.co", "Ryan Murphy",
         "The LinkedIn Sales Navigator integration worked for 2 months and stopped syncing yesterday. "
         "The status shows 'Connected' but no new contacts are coming through.",
         "LinkedIn Sales Navigator sync silently stopped after 2 months of working.", 0.83),

        ("API documentation seems outdated — v2 endpoints returning 404", "Integration", "P2", "NEUTRAL", "OPEN", None,
         "developer@buildco.dev", "Sam Okafor",
         "I'm building against your API docs at docs.novacrm.com/api/v2. "
         "Several endpoints listed are returning 404. Are these available on v2 or still v1 only?",
         "API v2 documentation discrepancy — several documented endpoints returning 404.", 0.79),

        ("Microsoft Teams notifications not working", "Integration", "P2", "NEUTRAL", "OPEN", None,
         "it@enterprise.com", "Hannah Webb",
         "We connected Microsoft Teams for notifications but they're not coming through. "
         "Slack notifications work fine. The Teams webhook URL is configured in settings.",
         "Microsoft Teams notifications failing — Slack integration works fine.", 0.82),

        # ── ONBOARDING (10) ───────────────────────────────────────────────────
        ("Getting started — how do I import my contacts", "Onboarding", "P3", "NEUTRAL", "DEFLECTED", None,
         "new@customer.com", "Emily Ross",
         "Hi, I just signed up yesterday. I have 2,000 contacts in a spreadsheet. "
         "What's the best way to import them into NovaCRM?",
         "New customer asking how to import contacts — answered by KB.", 0.97),

        ("SSO setup with Okta not working", "Onboarding", "P1", "FRUSTRATED", "IN_PROGRESS",
         "sarah@novacrm.com",
         "it@enterpriseclient.com", "Daniel Foster",
         "We're trying to set up SSO with Okta for our 500-user organization. "
         "The SAML assertion is being rejected by NovaCRM. "
         "We've followed the documentation exactly.",
         "Okta SSO SAML assertion rejected — 500-user enterprise blocked from login.", 0.90),

        ("Team invite emails not being received", "Onboarding", "P2", "FRUSTRATED", "OPEN", None,
         "hr@newcompany.com", "Sandra White",
         "I've sent invitations to 8 new team members but none of them are receiving the email. "
         "I've checked spam folders. All emails are @newcompany.com domain.",
         "Team invitation emails not being delivered to new domain.", 0.87),

        ("How to set up pipeline stages for our sales process", "Onboarding", "P3", "NEUTRAL", "DEFLECTED", None,
         "sales@b2bfirm.com", "Victor Huang",
         "We're new to NovaCRM and want to customize our pipeline. "
         "We have 7 stages in our sales process. How do I set these up?",
         "New customer needs help customizing pipeline stages.", 0.93),

        ("Role permissions setup for different team levels", "Onboarding", "P3", "NEUTRAL", "OPEN", None,
         "admin@mediumco.com", "Iris Nguyen",
         "We have 3 levels of users: Admins (full access), Managers (can see all team data), "
         "and Reps (can only see their own data). How do I configure these permissions?",
         "Customer needs help configuring role-based access control.", 0.85),

        ("How to connect our Gmail accounts", "Onboarding", "P3", "NEUTRAL", "DEFLECTED", None,
         "team@consulting.com", "Ben Carter",
         "We want to connect all 10 of our team's Gmail accounts to NovaCRM "
         "so emails are automatically logged. Is this done individually or as a team setting?",
         "Customer asking how to connect Gmail accounts for email logging.", 0.91),

        ("Import failed — CSV format error", "Onboarding", "P2", "FRUSTRATED", "OPEN", None,
         "admin@legalfirm.com", "Nancy Zhou",
         "I tried to import my contacts but keep getting 'Invalid CSV format' error. "
         "I followed the template exactly. Sending the CSV file for review.",
         "CSV import failing with format error despite following template.", 0.84),

        ("Need onboarding call — complex setup requirements", "Onboarding", "P2", "NEUTRAL", "OPEN", None,
         "ceo@complexorg.com", "Robert King",
         "We have very specific requirements: custom fields, multiple pipelines, "
         "SSO, and Salesforce bidirectional sync. Can we schedule a call with a solution engineer?",
         "Enterprise customer requesting dedicated onboarding support.", 0.82),

        ("Data migration from Pipedrive", "Onboarding", "P2", "NEUTRAL", "IN_PROGRESS",
         "james@novacrm.com",
         "ops@pipedrivemigrant.com", "Charlotte Davis",
         "We're migrating from Pipedrive and have exported our data. "
         "We have contacts, companies, deals, and activities. "
         "What's the recommended import order to preserve relationships?",
         "Pipedrive migration — customer needs import order guidance.", 0.86),

        ("Training resources for new team members", "Onboarding", "P3", "NEUTRAL", "OPEN", None,
         "training@growthhq.com", "George Miller",
         "We just added 15 new sales reps. Do you have video tutorials or a training guide "
         "we can share with them? A structured onboarding program would be ideal.",
         "Customer requesting training materials for 15 new users.", 0.78),

        # ── ACCOUNT (10) ──────────────────────────────────────────────────────
        ("Can't reset my password — no email received", "Account", "P2", "FRUSTRATED", "OPEN", None,
         "blocked@user.com", "Alice Thompson",
         "I've clicked 'Forgot Password' 4 times and haven't received any email. "
         "Not in spam either. I'm locked out and need access for a client meeting tomorrow.",
         "Password reset emails not being received — client meeting at risk.", 0.90),

        ("Need to transfer account ownership", "Account", "P2", "NEUTRAL", "OPEN", None,
         "outgoing@departing.com", "Frank Wilson",
         "I'm leaving the company and need to transfer account ownership to our new CRM admin. "
         "Her email is newadmin@company.com. I don't want to lose access before this is done.",
         "Account ownership transfer request — departing admin.", 0.83),

        ("Seat limit reached — can't add new user", "Account", "P2", "NEUTRAL", "DEFLECTED", None,
         "admin@growingteam.com", "Diana Brown",
         "We're trying to add our 11th user but get an error saying we've reached our seat limit. "
         "We're on the Starter plan which allows 10 seats. How do we add more?",
         "Seat limit reached — customer needs to add seats.", 0.95),

        ("2FA locked out after phone replacement", "Account", "P1", "FRUSTRATED", "OPEN", None,
         "user@securecompany.com", "Max Sterling",
         "I got a new phone and didn't save my 2FA backup codes. "
         "I can't log in and my admin is on vacation for 2 weeks. "
         "I need access urgently — I'm the backup admin.",
         "2FA lockout after phone replacement — no backup codes, admin unavailable.", 0.92),

        ("Delete my account and all data (GDPR)", "Account", "P1", "NEUTRAL", "ESCALATED",
         "james@novacrm.com",
         "gdpr@europeanuser.eu", "Klaus Müller",
         "I'm invoking my right to erasure under GDPR Article 17. "
         "Please delete my personal data and confirm in writing within 30 days.",
         "GDPR right to erasure request — escalated to data privacy team.", 0.88),

        ("Admin account was suspended — need immediate reinstatement", "Account", "P0", "ANGRY", "ESCALATED",
         "sarah@novacrm.com",
         "ceo@bigclient.com", "Thomas Black",
         "Our company's admin account was suspended this morning. "
         "We have NO access to NovaCRM at all — 50 users are locked out. "
         "We're a paying Enterprise customer. This needs to be fixed NOW.",
         "P0: Entire 50-user Enterprise account suspended — complete lockout.", 0.98),

        ("How do I change my email address", "Account", "P3", "NEUTRAL", "DEFLECTED", None,
         "user@emailchange.com", "Lucy Park",
         "I changed my work email address and need to update my NovaCRM login email. "
         "Where do I change this in the account settings?",
         "Customer wants to update login email address.", 0.94),

        ("Security concern — suspicious login attempt", "Account", "P1", "ANGRY", "OPEN", None,
         "security@concerned.com", "Ivan Novak",
         "I received an email saying someone logged into my account from Russia at 3am. "
         "I don't recognize this access. I've already changed my password. "
         "Can you check the logs and tell me what they accessed?",
         "Unauthorized login attempt from unknown location — potential security breach.", 0.93),

        ("Need to add a co-admin to manage billing", "Account", "P3", "NEUTRAL", "OPEN", None,
         "finance@bigteam.com", "Rosa Martinez",
         "Our finance team needs access to manage billing but we don't want them "
         "to have full admin access. Is there a billing-only admin role?",
         "Customer requesting billing-only admin role for finance team.", 0.81),

        ("Account showing wrong company name", "Account", "P3", "NEUTRAL", "RESOLVED",
         "priya@novacrm.com",
         "admin@rebrand.io", "Jake Summers",
         "We rebranded from 'Acme Tools' to 'Vertex Solutions' in January. "
         "Our NovaCRM account still shows the old name everywhere. How do I update this?",
         "Company name rebrand update needed across account.", 0.86),
    ]

    # ── UNCLASSIFIED TICKETS FOR AI TRIAGE DEMO ────────────────────────────
    # These tickets have no AI classification yet - perfect for testing "Run AI Triage"
    unclassified_tickets = [
        ("Our integration with Salesforce keeps disconnecting", None, None, None, "OPEN", None,
         "integrations@salesforceuser.com", "Rebecca Wong",
         "We set up the Salesforce integration last week and it was working fine. "
         "Now we're getting sync errors every few hours. The error says 'Token expired'. "
         "This is blocking our sales team's workflow."),

        ("Can you help with custom field mapping for our import?", None, None, None, "OPEN", None,
         "ops@customfieldco.com", "Michael Chen",
         "I'm trying to import 10,000 contacts from our old system. "
         "The old system has some custom fields that don't match NovaCRM's standard fields. "
         "Can I map custom fields during import or do I need to create them first?"),

        ("We're getting HTTP 429 errors from the API", None, None, None, "OPEN", None,
         "engineering@apiuser.io", "Elena Rodriguez",
         "Our integration is hitting rate limits. We're getting HTTP 429 (Too Many Requests) errors. "
         "What's the rate limit per minute? Can it be increased for our use case?"),

        ("Dashboard widgets disappeared after update", None, None, None, "OPEN", None,
         "analyst@dashboard.co", "David Lee",
         "After the latest app update, 3 of our custom dashboard widgets are gone. "
         "We had KPI metrics configured that took hours to set up. "
         "Is there a way to restore them?"),

        ("Email campaign not sending to contacts in a specific segment", None, None, None, "OPEN", None,
         "marketing@segmentmail.com", "Jennifer Martinez",
         "We created an email campaign and targeted a segment of 500 contacts. "
         "The campaign shows as 'Sent' but our marketing team says they received 0 opens. "
         "We checked the segment manually and the contacts are definitely there."),

        ("Two-factor authentication not working on mobile", None, None, None, "OPEN", None,
         "mobile@2fauser.com", "Samuel Thompson",
         "I have 2FA enabled. It works on desktop but when I try to log in on my iPhone, "
         "the authenticator app code doesn't work. I get 'Invalid OTP' error every time."),

        ("Can we get historical data from before our migration?", None, None, None, "OPEN", None,
         "data@historical.com", "Patricia Johnson",
         "We migrated to NovaCRM 3 months ago. Our previous CRM data (contacts from the past 2 years) "
         "is archived but we need to run reports on it. Can you help us recover or import that data?"),

        ("Your pricing page shows a feature we don't have access to", None, None, None, "OPEN", None,
         "sales@pricingissue.com", "William Anderson",
         "We're on the Professional plan. Your pricing page says Professional includes 'Advanced Reporting'. "
         "But we don't see that feature in our account. Are we supposed to enable it somewhere?"),
    ]

    # Create pre-classified tickets
    for (subject, category, urgency, sentiment, status, assigned_to,
         customer_email, customer_name, body, ai_summary, ai_confidence) in tickets:
        days_ago = random.uniform(0.1, 28)
        db.create_ticket(
            subject=subject, body=body,
            customer_name=customer_name, customer_email=customer_email,
            status=status, category=category, urgency=urgency, sentiment=sentiment,
            ai_category=category, ai_urgency=urgency, ai_sentiment=sentiment,
            ai_confidence=ai_confidence, ai_summary=ai_summary,
            assigned_to=assigned_to,
            created_at=_ago(days_ago),
        )

    # Create unclassified tickets (for "Run AI Triage" demo)
    for (subject, category, urgency, sentiment, status, assigned_to,
         customer_email, customer_name, body) in unclassified_tickets:
        days_ago = random.uniform(0.1, 28)
        db.create_ticket(
            subject=subject, body=body,
            customer_name=customer_name, customer_email=customer_email,
            status=status, category=category, urgency=urgency, sentiment=sentiment,
            # Leave AI fields unset - these will be classified by "Run AI Triage"
            ai_category=None, ai_urgency=None, ai_sentiment=None,
            ai_confidence=None, ai_summary=None,
            assigned_to=assigned_to,
            created_at=_ago(days_ago),
        )

    # Seed pre-generated AI draft responses for the first 5 tickets
    _seed_ai_responses()


def _seed_ai_responses() -> None:
    drafts = [
        (1, "Dear Sarah,\n\nThank you for reaching out, and I sincerely apologize for the duplicate charge on your account. I completely understand how alarming it is to see an unexpected charge, and we want to resolve this as quickly as possible.\n\nI've flagged your account for immediate review. Our billing team will investigate the duplicate charge for Invoice #INV-2024-10-0045 and process a full refund to your original payment method within 3-5 business days.\n\nYou'll receive a confirmation email once the refund is processed. If you have any further questions in the meantime, please don't hesitate to reach out.\n\nBest regards,\nSarah\nNovaCRM Support"),
        (2, "Hi Mark,\n\nThanks for reaching out! Downloading your invoices is quick and easy.\n\nHere's how: Go to Settings → Billing → Invoice History. You'll see all your past invoices listed by date. Click the download icon (PDF) next to the September invoice you need.\n\nIf you need to access invoices older than 12 months, just reply to this email and we'll send them directly.\n\nHope that helps!\n\nBest regards,\nNovaCRM Support"),
        (3, "Hi Lisa,\n\nCongratulations on growing the team! Moving from Starter to Business is a great step.\n\nHere's what the Business plan includes: unlimited contacts, up to 50 users, advanced reporting, custom pipelines, and priority support. Pricing is $49/seat/month (or $39/seat/month on annual).\n\nYou can upgrade directly from Settings → Billing → Change Plan. The upgrade takes effect immediately, and you'll only be charged the prorated difference for the current billing period.\n\nWould you like me to apply a 20% first-year discount for your upgrade? Just let me know!\n\nBest regards,\nJames\nNovaCRM Support"),
        (4, "Hi Tom,\n\nI understand the surprise — let me explain what happened.\n\nYour NovaCRM subscription is set up on annual billing, which means you're charged once per year on your renewal date. Your renewal date was today, which triggered the $2,400 charge.\n\nIf you'd like to switch to monthly billing going forward, I can make that change for your next cycle. Note that monthly billing is slightly higher ($240/month vs. $2,400/year).\n\nIf you believe this renewal should not have occurred, please let me know and our billing team can review your cancellation request.\n\nBest regards,\nPriya\nNovaCRM Support"),
        (5, "Hi Anna,\n\nThank you for reaching out, and no worries — we're happy to help with the downgrade.\n\nGood news: your data is fully preserved when changing plans. All contacts, deals, and history remain intact. The Starter plan supports up to 10 seats, so with 8 seats you'll be within the limit.\n\nDowngrades take effect at the start of your next billing cycle. To proceed: Settings → Billing → Change Plan → Select Starter → Confirm.\n\nIs there anything else I can help with, or anything we can do to make NovaCRM work better within your budget?\n\nBest regards,\nNovaCRM Support"),
    ]
    for ticket_id, draft in drafts:
        db.add_ai_response(ticket_id, draft, "gpt-4o")


def seed():
    """Public entry point for re-seeding from the UI."""
    db.init_db()
    db.clear_all()
    init()


if __name__ == "__main__":
    seed()
    stats = db.get_stats()
    unclassified = len([t for t in db.get_all_tickets() if not t.get("ai_category")])
    print(f"✓ {stats['total']} tickets seeded ({unclassified} unclassified for AI Triage demo)")
    print(f"  Open: {stats['open']} | Deflected: {stats['deflected']} | "
          f"Resolved: {stats['resolved']} | Escalated: {stats['escalated']}")
    kb = db.get_kb_articles()
    print(f"✓ {len(kb)} KB articles seeded")
