package main

func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	var rand_range [MAXASSIGNS]int
	var rand_limit int = 0

	for ii := range rand_range {
		rand_range[ii] = ii
		if ii < dispatch.AssignsLen && dispatch.Assigns[ii].StationsLen > 0 {
			rand_range[ii], rand_range[rand_limit] = rand_range[rand_limit], ii
			rand_limit += 1
		}
	}
	rand.Shuffle(rand_limit, func(i, j int) {
		rand_range[i], rand_range[j] = rand_range[j], rand_range[i]
	})

	for jj := range oris {
		bestIdx := -1
		bestCost := 1e18
		for _, ii := range rand_range {
			if ii >= dispatch.AssignsLen && dispatch.Assigns[dispatch.AssignsLen].StationsLen > 0 {
				continue
			}
			if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				dispatch.Assigns[ii].RemoveShip(total_ship + jj)
				continue
			}
			oldCost := dispatch.Assigns[ii].Cost
			dispatch.Assigns[ii].GenRoute()
			newCost := dispatch.Assigns[ii].Cost
			if newCost >= 0 && (newCost-oldCost) < bestCost {
				bestCost = newCost - oldCost
				bestIdx = ii
			}
			dispatch.Assigns[ii].RemoveShip(total_ship + jj)
			dispatch.Assigns[ii].GenRoute()
		}
		if bestIdx == -1 {
			bestIdx = dispatch.AssignsLen
		}
		dispatch.Assigns[bestIdx].AddShip(total_ship+jj, oris[jj], dess[jj])
		dispatch.Assigns[bestIdx].GenRoute()
		if bestIdx >= dispatch.AssignsLen {
			dispatch.AssignsLen += 1
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}
