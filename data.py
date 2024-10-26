from dataclasses import dataclass
from datetime import datetime
from api_client import AuthenticatedAPIClient
from json import loads
import re


@dataclass
class Module:
    name: str
    parent: str
    kind: str
    url: str
    due_date: datetime
    allow_submissions_from_date: datetime

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            parent=data["parent"],
            kind=data["kind"],
            url=data["url"],
            due_date=data["due_date"],
            allow_submissions_from_date=data["allow_submissions_from_date"],
        )


class DataRepository:
    def __init__(self, api: AuthenticatedAPIClient, site_info, user_id):
        self.api = api
        self.site_info = site_info
        self.user_id = user_id

    @classmethod
    async def create(cls, api: AuthenticatedAPIClient):
        self = cls(api, None, None)
        self.site_info = await self.fetch_site_info()
        self.user_id = self.site_info["userid"]
        return self

    async def fetch_site_info(self):
        response = await self.api.call_ajax("core_webservice_get_site_info")
        return response

    async def get_assignments(self):
        response = await self.api.call_ajax("mod_assign_get_assignments")
        return response

    async def get_enrolled_courses_by_timeline(self):
        response = await self.api.call_ajax(
            "core_course_get_enrolled_courses_by_timeline_classification",
            classification="all",
            sort="fullname",
        )
        return response

    async def get_enrolled_courses(self, user_id=None) -> dict:
        if user_id is None:
            user_id = self.user_id

        response = await self.api.call_ajax(
            "core_enrol_get_users_courses", userid=user_id
        )
        return response

    async def get_course_contents(self, course_id):
        response = await self.api.call_ajax(
            "core_course_get_contents", courseid=course_id
        )
        return response


def filter_modules_with_date(contents) -> list[Module]:
    found = []
    for content in contents:
        for module in content["modules"]:
            if module["modname"] == "label" or not module["uservisible"]:
                continue

            base_output = {
                "name": module["name"],
                "parent": content["name"],
                "kind": module["modname"],
                "url": module["url"],
            }

            if "dates" in module and len(module["dates"]) >= 2:
                allow_submissions_from_date = datetime.fromtimestamp(
                    module["dates"][0]["timestamp"]
                )
                due_date = datetime.fromtimestamp(module["dates"][1]["timestamp"])
                found.append(
                    base_output
                    | {
                        "due_date": due_date,
                        "allow_submissions_from_date": allow_submissions_from_date,
                    }
                )
                continue

            if "customdata" in module and "duedate" in (
                custom_data := loads(module["customdata"])
            ):
                due_date = datetime.fromtimestamp(int(custom_data["duedate"]))
                allow_submissions_from_date = datetime.fromtimestamp(
                    int(custom_data["allowsubmissionsfromdate"])
                )
                found.append(
                    base_output
                    | {
                        "due_date": due_date,
                        "allow_submissions_from_date": allow_submissions_from_date,
                    }
                )
                continue

            # Fallback behaviour - O puro suco da gambiarra
            # Eu sei que isso é uma gambiarra, mas é o que tem pra hoje
            # Veyr, isso daqui é só para filosofiaKKKKKKKKKKKKKK
            # Porque a data de entrega é sempre no formato "Nome. dd/mm - dd/mm"
            # E não, o Vinicius não tá definidindo a data de entrega no quiz do módulo
            # Porra vei, perdi um moodle por causa disso KKKKKKKKKKKKK
            # Vai tomar no cu, pelo menos tá funcionando, por enquanto.
            q_regex = r"(?P<qNome>\w*. \d{1,2}) \((?P<abre>\d{2}/\d{2})\s*-\s*(?P<fecha>\d{2}/\d{2})\)"

            if match := re.match(q_regex, module["name"]):
                due_date = datetime.strptime(
                    f"{match.group('fecha')}/{datetime.now().year}", "%d/%m/%Y"
                )
                allow_submissions_from_date = datetime.strptime(
                    f"{match.group('abre')}/{datetime.now().year}", "%d/%m/%Y"
                )
                found.append(
                    base_output
                    | {
                        "name": match.group("qNome"),
                        "due_date": due_date,
                        "allow_submissions_from_date": allow_submissions_from_date,
                    }
                )
                continue

    return [Module.from_dict(module) for module in found]


def find_available_modules(modules: list[Module]) -> list:
    return [
        module
        for module in modules
        if module.allow_submissions_from_date < datetime.now() < module.due_date
    ]
