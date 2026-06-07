import shutil


def create_zip():

    shutil.make_archive(
        "generated_app",
        "zip",
        "generated_app"
    )

    return "generated_app.zip"