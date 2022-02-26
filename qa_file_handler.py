class Save:

    @staticmethod
    def secure_save(file_path, data):
        with open(file_path, 'w') as file:
            file.write(data)
            file.close()
