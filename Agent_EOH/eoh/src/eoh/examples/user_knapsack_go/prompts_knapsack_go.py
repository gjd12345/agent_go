class GetPrompts:
    def __init__(self):
        self.prompt_task = (
            "You need to write a Go function `SelectItems` for a 0/1 knapsack problem.\n"
            "The function signature must be:\n"
            "```go\n"
            "func SelectItems(items []Item, capacity int) []bool\n"
            "```\n"
            "Return exactly len(items) booleans. A true value means the item is selected.\n"
            "The selected total weight must not exceed capacity. Maximize selected total value.\n"
            "Available type:\n"
            "```go\n"
            "type Item struct { Weight int; Value int }\n"
            "```\n"
        )
        self.prompt_func_name = "SelectItems"
        self.prompt_func_inputs = ["items", "capacity"]
        self.prompt_func_outputs = ["[]bool"]
        self.prompt_inout_inf = "- Inputs: items []Item, capacity int\n- Output: []bool\n"
        self.prompt_other_inf = (
            "CRITICAL: Return ONLY Go code. Do not wrap in markdown. Do not include any explanations.\n"
            "Return ONLY the method definition `func SelectItems(items []Item, capacity int) []bool { ... }`.\n"
            "Do not write `package main` and do not add any imports.\n"
            "The returned slice length must equal len(items).\n"
            "Never select items whose total weight exceeds capacity.\n"
        )

    def get_task(self):
        return self.prompt_task

    def get_func_name(self):
        return self.prompt_func_name

    def get_func_inputs(self):
        return self.prompt_func_inputs

    def get_func_outputs(self):
        return self.prompt_func_outputs

    def get_inout_inf(self):
        return self.prompt_inout_inf

    def get_other_inf(self):
        return self.prompt_other_inf
