""" Mix Sampling

This module contains a class that implements the mix sampling strategy that 
mix the top suggestions from different strategies

"""
import numpy as np

from libact.base.interfaces import BatchQueryStrategy
from libact.utils import inherit_docstring_from, seed_random_state, zip


class MixSampling(BatchQueryStrategy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query_strategies_ = kwargs.pop('query_strategies', None)
        if self.query_strategies_ is None:
            raise TypeError(
                "__init__() missing required keyword-only argument: "
                "'query_strategies'"
            )
        elif not self.query_strategies_:
            raise ValueError("query_strategies is empty")

        # check if query_strategies share the same dataset
        for qs in self.query_strategies_:
            if qs.dataset != self.dataset:
                raise ValueError("query_strategies should share the same"
                                 "dataset instance with mix sampling")
            if not isinstance(qs, BatchQueryStrategy):
                raise ValueError("query_strategies should all support batch"
                                 "query.")

        if isinstance(self.query_strategies_, list):
            self.query_strategies_ = {
                qs: 1 / len(self.query_strategies_)
                for qs in self.query_strategies_
            }
        elif isinstance(self.query_strategies_, dict):
            assert sum([p for _, p in self.query_strategies_.items()]) == 1.,\
                "Sum of the weight of the strategies should be 1.0."
        else:
            raise ValueError("Query strategies should be either a list or "
                             "dictionary.")

        random_state = kwargs.pop('random_state', None)
        self.random_state_ = seed_random_state(random_state)

    def make_query(self, n_ask=1, **kwargs):
        candidates = {
            qs: qs.make_query(n_ask=n_ask, **kwargs)
            for qs in self.query_strategies_
        }
        if n_ask == 1:
            candidates = {qs: [v] for qs, v in candidates.items()}

        n_need = n_ask
        query_idx = set()
        while n_need > 0:
            pick = []
            if any([p*n_need >= 1 for _, p in self.query_strategies_.items()]):
                for qs in candidates:
                    n_picking = int(self.query_strategies_[qs] * n_need)
                    pick.extend(candidates[qs][:n_picking])
                    candidates[qs] = candidates[qs][n_picking:]
            else:
                # sample
                qss, ps = list(zip(*self.query_strategies_.items()))
                n_sampling = self.random_state_.choice(len(qss),
                                                       size=n_need, p=ps)
                for j, n in zip(*np.unique(n_sampling, return_counts=True)):
                    pick.extend(candidates[qss[j]][:n])
                    candidates[qss[j]] = candidates[qss[j]][n:]

            pick = set(pick)
            n_need -= len(pick - query_idx)
            query_idx = query_idx.union(pick)

        return list(query_idx) if n_ask > 1 else query_idx.pop()
