import asyncio
from api_client import APIClient
from config import load_config
from data import (
    DataRepository,
    find_available_modules,
    filter_modules_with_date,
    Module,
)
from __init__ import __version__

config = load_config()


async def fetch_available_modules(repository: DataRepository):
    print(
        f" 🏕️ Campus: {repository.site_info['sitename']}\n 🧑 Usuário: {repository.site_info['firstname']} {repository.site_info['lastname']}"
    )

    print("📟 Obtendo cursos... ", end=" ", flush=True)
    enrolled_courses = await repository.get_enrolled_courses()
    print(f"Encontrado {len(enrolled_courses)} cursos.", flush=True)

    all_modules = {}

    print("📲 Obtendo módulos...", end="", flush=True)
    for course in enrolled_courses:
        print(".", end="", flush=True)

        contents = await repository.get_course_contents(course["id"])

        modules = filter_modules_with_date(contents)
        all_modules |= {course["fullname"]: modules}

    print(
        f" Encontrado {sum(len(modules) for modules in all_modules.values())} modulos.",
        flush=True,
    )

    available_modules = {} | {
        course: find_available_modules(modules)
        for course, modules in all_modules.items()
    }
    return available_modules


# Transform ID - COURSE NAME - EXTRA INFO to COURSE NAME
def get_simplified_course_name(course_name: str):
    return course_name.split(" - ")[1]


def construct_message(available_modules: dict[str, list[Module]]):
    todo_fmt = ""
    emojis = {
        "assign": "📝",
        "forum": "💬",
        "quiz": "🧠",
        "url": "🔗",
        "page": "📄",
        "book": "📚",
        "folder": "📁",
        "resource": "📦",
        "label": "🏷️",
        "lesson": "📖",
        "choice": "🤔",
        "feedback": "📣",
        "workshop": "🔨",
        "glossary": "📖",
        "wiki": "📖",
        "survey": "📊",
        "data": "📊",
        "attendance": "📋",
        "scorm": "📦",
        "h5pactivity": "🎮",
    }

    available_modules_count = sum(
        len(modules) for modules in available_modules.values()
    )
    for course, modules in available_modules.items():
        for task in modules:
            de = task.allow_submissions_from_date.strftime("%d/%m %H:%M")
            ate = task.due_date.strftime("%d/%m %H:%M")
            todo_fmt += f"📚 {get_simplified_course_name(course)}\n"
            todo_fmt += f" ➤ {emojis[task.kind]} {task.name} (De: {de} até {ate})\n"
            todo_fmt += f"> Acesse em: {task.url}\n\n"

    output = "📅✨ MOODLES ABERTOS 🚀\n"
    output += f"> 🎉 Uau! Temos {available_modules_count} atividades incríveis prontinhas para vocês explorar e entregar! 🚀\n\n"
    output += todo_fmt
    output += f"> 📚 Acesse o Moodle em: {config['Moodle']['AppURL']}\n"
    output += f"> Criada com carinho pela Pache `{__version__}` 🎀"

    return output


async def main():
    app_url = config["Moodle"]["AppURL"]
    print(f"🎀 Pache `{__version__}` - Sua copilota do Moodle \n")

    async with APIClient(app_url) as unauthenticated_api:
        print("🗨️ Iniciando sessão... ", end="", flush=True)
        token = await unauthenticated_api.login(
            username=config["Account"]["Username"],
            password=config["Account"]["Password"],
        )
        print("OK!")

        async with unauthenticated_api.with_token(token) as rest:
            print("🪢 Obtendo informaçôes básicas... ", end=" ", flush=True)
            repository = await DataRepository.create(rest)
            print("OK!")

            print("🔍 Buscando atividades disponíveis... ")

            available_modules = await fetch_available_modules(repository)

            print("\n" * 2)

            print(construct_message(available_modules))


if __name__ == "__main__":
    asyncio.run(main())
