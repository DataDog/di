from di.utils import ensure_parent_dir_exists


class File:
    def __init__(self, file_path, contents, binary=False):
        self.file_path = file_path
        self.contents = contents
        self.write_mode = 'wb' if binary else 'w'

    def write(self):
        ensure_parent_dir_exists(self.file_path)

        with open(self.file_path, self.write_mode) as f:
            if isinstance(self.contents, str):
                f.write(self.contents)
            else:
                f.writelines(self.contents)
