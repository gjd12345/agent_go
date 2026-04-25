class GetPrompts:
    def __init__(self):
        self.prompt_task = (
            "You need to write a Go function `InsertShips` to optimize vehicle routing assignments.\n"
            "The function signature must be:\n"
            "```go\n"
            "func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch\n"
            "```\n"
            "The goal is to minimize the `final cost` output by the simulation.\n"
            "The input struct and helper functions available are:\n"
            "```go\n"
            "const MAXASSIGNS = 32\n"
            "type Station struct{\n"
            "    X         int\n"
            "    Y         int\n"
            "    TimeStart int\n"
            "    TimeEnd   int\n"
            "    ReqCode   int\n"
            "    Load      int\n"
            "}\n"
            "type Dispatch struct {\n"
            "    Assigns    [MAXASSIGNS]Assign\n"
            "    AssignsLen int\n"
            "    TotalCost  float64\n"
            "    AccumulatedCost float64\n"
            "}\n"
            "type Assign struct { ... }\n"
            "func cal_dis(st1, st2 Station) float64\n"
            "// Available methods on Assign: \n"
            "// func (assign *Assign) AddShip(id int, ori, des Station) bool\n"
            "// func (assign *Assign) RemoveShip(id int)\n"
            "// func (assign *Assign) GenRoute()\n"
            "// Fields on Assign: StationCurrent Station, Cost float64, etc.\n"
            "// Method on Dispatch: \n"
            "// func (dispatch *Dispatch) RenewnTotalCost()\n"
            "```\n"
        )
        self.prompt_func_name = "InsertShips"
        self.prompt_func_inputs = ["dispatch", "oris", "dess", "total_ship"]
        self.prompt_func_outputs = ["Dispatch"]
        self.prompt_inout_inf = (
            "- Inputs: dispatch Dispatch, oris []Station, dess []Station, total_ship int\n"
            "- Output: Dispatch\n"
        )
        self.prompt_other_inf = (
            "CRITICAL: Return ONLY Go code. Do not wrap in markdown. Do not include any explanations.\n"
            "Return ONLY the method definition `func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch { ... }`.\n"
            "Do not write `package main` and do not add any imports.\n"
            "Process every order index in `oris`/`dess`; never stop the outer order loop early when one order cannot be inserted.\n"
            "If no improved insertion is found for an order, fall back to a safe seed-style insertion instead of silently dropping it.\n"
            "Always call `dispatch.RenewnTotalCost()` immediately before returning the dispatch.\n"
            "Do not print, mock, overwrite, or directly optimize the final cost output; improve only the assignment logic.\n"
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
