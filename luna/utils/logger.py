class Logger:
    COLORS = {
        "HEADER": "\033[95m",
        "DEBUG": "\033[36;1m",
        "INFO": "\033[92;1m",
        "WARNING": "\033[93;1m",
        "CRITICAL": "\033[38;5;160m",
        "ERROR": "\033[31;1m",
        "ENDC": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
    }

    @staticmethod
    def log(level, *args):
        text_color = "\033[91m" if level.upper() == "CRITICAL" else "\033[37m"
        level_color = Logger.COLORS.get(level.upper(), "")
        endc = Logger.COLORS["ENDC"]
        print(f"[{level_color}{level.upper()}{endc}]", text_color, *args, endc)

    @staticmethod
    def info(*args):
        Logger.log("INFO", *args)

    @staticmethod
    def debug(*args):
        Logger.log("DEBUG", *args)

    @staticmethod
    def warning(*args):
        Logger.log("WARNING", *args)

    @staticmethod
    def warn(*args):
        Logger.warning(*args)

    @staticmethod
    def error(*args):
        Logger.log("ERROR", *args)

    @staticmethod
    def critical(*args):
        Logger.log("CRITICAL", *args)


logger = Logger  # backwords compatibility
