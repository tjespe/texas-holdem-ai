import os
import inquirer


def login():
    lines = (
        [l.strip() for l in open("./users.txt", "r").readlines()]
        if os.path.exists("./users.txt")
        else []
    )
    users_with_passwords = [l.split(",") for l in lines if l]
    usernames = [username for username, pwd in users_with_passwords]
    options = usernames + ["Create new user"]
    questions = [
        inquirer.List(
            "username",
            message="What is your name?",
            choices=options,
            autocomplete=True,
            carousel=True,
            default=options[0],
        ),
    ]
    answers = inquirer.prompt(questions)
    if answers is None:
        print("Bye!")
        return exit(0)
    answer = answers["username"]
    if answer == "Create new user":
        questions = [
            inquirer.Text("username", message="Enter your name"),
            inquirer.Password("password", message="Enter a password"),
        ]
        answers = inquirer.prompt(questions)
        uname = answers["username"]
        if uname in usernames:
            print("User already exists")
            return login()
        with open("users.txt", "a") as f:
            pwd = answers["password"]
            f.write(f"\n{uname},{pwd}")
        return uname
    pwd = inquirer.password("Enter your password")
    pwd_map = dict(users_with_passwords)
    if pwd_map.get(answer) == pwd:
        return answer
    print("Incorrect password")
    return login()
