import qa_prompts, qa_functions


def install_addon_themes():
    file_urls = qa_functions.OnlineFiles.Addons.Theme.all_files
    for url in file_urls:
        name = url.split('/')[-1]
        try:
            qa_prompts.InputPrompts.DownloadFile(
                qa_prompts.DownloadPacket(
                    f'{qa_functions.App.appdata_dir}\\{qa_functions.Files.ad_theme_folder}\\{name}'.replace('/', '\\'),
                    f"Downloading {name}",
                    "Please wait as the theme file is downloading..."
                ),
                url
            )

        except Exception as E:
            qa_prompts.MessagePrompts.show_error(qa_prompts.InfoPacket(f"Failed to install {name}: {E}"))


def RunAddonsInstaller(*args, **kwargs):
    install_addon_themes()
    return None
