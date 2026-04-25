PROJECT="dvrp"

build:
	go build -o mainbin main.go routing.go;

build-genetic:
	go build -o mainbin_genetic ./genetic/main_genetic.go ./genetic/routing_genetic.go;

build-all: build build-genetic

test: build
	for file in ./solomon_benchmark/rc1*.json; \
	do \
	    echo $$file; \
	    ./mainbin $$file 10 | tail -2  | xargs | sed 's/final\|cost//g' | sed 's/\ /,/g' | sed 's/,,,/,/g' | xargs -I {} echo ${file##*/},{} >> final_result.txt; \
	done

test-genetic: build-genetic
	for file in ./solomon_benchmark/rc1*.json; \
	do \
	    echo $$file; \
	    ./mainbin_genetic $$file 10 | tail -2  | xargs | sed 's/final\|cost//g' | sed 's/\ /,/g' | sed 's/,,,/,/g' | xargs -I {} echo ${file##*/},{} >> final_result_genetic.txt; \
	done

