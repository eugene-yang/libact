"""Random Sampling
"""
import numpy as np
from libact.base.interfaces import BatchQueryStrategy
from libact.utils import inherit_docstring_from, seed_random_state, zip


class RandomSampling(BatchQueryStrategy):

    r"""Random sampling

    This class implements the random query strategy. A random entry from the
    unlabeled pool is returned for each query.

    Parameters
    ----------
    random_state : {int, np.random.RandomState instance, None}, optional (default=None)
        If int or None, random_state is passed as parameter to generate
        np.random.RandomState instance. if np.random.RandomState instance,
        random_state is the random number generate.

    Attributes
    ----------
    random_states\_ : np.random.RandomState instance
        The random number generator using.

    Examples
    --------
    Here is an example of declaring a RandomSampling query_strategy object:

    .. code-block:: python

       from libact.query_strategies import RandomSampling

       qs = RandomSampling(
                dataset, # Dataset object
            )
    """

    def __init__(self, dataset, **kwargs):
        super(RandomSampling, self).__init__(dataset, **kwargs)

        random_state = kwargs.pop('random_state', None)
        self.random_state_ = seed_random_state(random_state)

    @inherit_docstring_from(BatchQueryStrategy)
    def make_query(self, n_ask=1, **kwargs):
        dataset = self.dataset
        unlabeled_entry_ids = dataset.get_unlabeled_idx()
        entry_id = self.random_state_.choice(unlabeled_entry_ids, n_ask)
        return entry_id if n_ask > 1 else entry_id[0]
