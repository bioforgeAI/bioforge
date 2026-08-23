# benchmarks/test_sequence.py
from bioforge import DnaSequence


class TestDnaSequenceBenchmark:
    def test_new_benchmark(self, benchmark):
        seq_str = "ATGC" * 10_000  # 40k bases
        benchmark(DnaSequence, seq_str)

    def test_getitem_benchmark(self, benchmark):
        seq = DnaSequence("ATGC" * 10_000)
        benchmark(lambda: [seq[i] for i in range(1_000)])

    def test_reverse_complement_benchmark(self, benchmark):
        seq = DnaSequence("ATGC" * 10_000)
        benchmark(seq.reverse_complement)
