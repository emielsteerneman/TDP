from time import time, sleep

class SimpleProfiler:
    def __init__(self) -> None:
        self.measurements = {}
        self.current_time_start = None
        self.current_label = None

        self.aggregation = {}

    def start(self, label:str):
        if self.current_label is not None:
            self.stop()
        
        self.current_label = label
        self.current_time_start = time()

    def stop(self):
        time_stop = time()

        if self.current_label is None: return

        if self.current_label not in self.measurements:
            self.measurements[self.current_label] = []

        if self.current_label not in self.aggregation:
            self.aggregation[self.current_label] = 0

        duration = time_stop - self.current_time_start

        self.measurements[self.current_label].append(duration)
        self.aggregation[self.current_label] += duration
    
        self.current_label = None

    def print_statistics(self):
        total_duration = sum(self.aggregation.values())

        print("\n==== Profiler statistics:")
        print(f"Total duration: {total_duration:.4f} seconds")
        for label, duration in self.aggregation.items():
            n = len(self.measurements[label])
            print(f"  {label.rjust(40)} - {duration:.4f}s    {duration/total_duration:.2%}    #{n}    mean={duration/n:.4f}s")

if __name__ == "__main__":
    print("Testing profiler")
    p = SimpleProfiler()
    p.start("l1")
    print("l1")
    sleep(0.5)
    p.start("l2")
    print("l2")
    sleep(1)
    p.stop()
    sleep(1)

    p.start("l2")
    print("l2")
    sleep(2)
    p.stop()
    
    p.print_statistics()