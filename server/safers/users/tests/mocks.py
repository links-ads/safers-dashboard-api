"""
mock data to use during development/testing
"""

MOCK_ORGANIZATIONS_DATA = [
    {
        "id": 1,
        "shortName": "TO",
        "name": "Test Organization",
        "description": "This is a test organization",
        "webSite": None,
        "logoUrl": None,
        "parentId": None,
        "parentName": "",
        "membersHaveTaxCode": False,
        "hasChildren": False
    },
    {
        "id": 2,
        "shortName": "SP",
        "name": "SAFERS Partners",
        "description": "Organization for partners of SAFERS",
        "webSite": None,
        "logoUrl": None,
        "parentId": None,
        "parentName": "",
        "membersHaveTaxCode": False,
        "hasChildren": False
    },
    {
        "id": 4,
        "shortName": "SFR",
        "name": "Safers",
        "description": "Father organization, can be used to send notifications to child organizations",
        "webSite": None,
        "logoUrl": "",
        "parentId": None,
        "parentName": "",
        "membersHaveTaxCode": False,
        "hasChildren": True
    },
]  # yapf: disable

MOCK_ROLES_DATA = [
    {
        "id": "b1dd2c4d-b030-4f86-932f-aa882f94bcc9",
        "name": "administrator",
        "description": "Administrator of SAFERS",
        "isDefault": False,
        "isSuperRole": True,
    },
    {
        "id": "83b983ec-6667-4e2e-9f4d-7a6a8b743284",
        "name": "citizen",
        "description": "citizen",
        "isDefault": True,
        "isSuperRole": False,
    },
    {
        "id": "e659aa96-0f15-480b-8eb1-58bc8ab5edaf",
        "name": "decision_maker",
        "description": "Decision Maker: sits in a control rooms during emergency, monitoring the situation",
        "isDefault": False,
        "isSuperRole": False,
    },
    {
        "id": "4383a40a-59ae-4dc2-9d47-a8db0909e9c0",
        "name": "first_responder",
        "description": "On-field role: First Responders can make reports and accomplish missions",
        "isDefault": False,
        "isSuperRole": False,
    },
    {
        "id": "9dafd582-9b08-40a7-9e35-a261d3ffae4a",
        "name": "organization_manager",
        "description": "Organization Manager: manages everything within his/her Organization in SAFERS",
        "isDefault": False,
        "isSuperRole": False,
    },
    {
        "id": "a18a8b7b-3129-440b-849c-ed9b1fae90b7",
        "name": "team_leader",
        "description": "Like First Responder, but with more powers",
        "isDefault": False,
        "isSuperRole": False,
    }
]  # yapf: disable