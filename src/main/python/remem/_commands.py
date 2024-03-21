class Command:
    def get_name(self) -> str:
        return 'this is an abstract method'

    def get_description(self) -> str:
        return 'this is an abstract method'

    def run(self, user_input: str) -> None:
        pass
