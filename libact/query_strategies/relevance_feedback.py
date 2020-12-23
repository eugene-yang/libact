import numpy as np 

from libact.base.interfaces import BatchQueryStrategy, ContinuousModel


class RelevanceFeedbackSampling(BatchQueryStrategy):
    def __init__(self, *args, **kwargs):
        super(RelevanceFeedbackSampling, self).__init__( *args, **kwargs )

        if self.dataset.get_num_of_labels() > 2:
            raise TypeError("Relevance feedback sampling only supports binary classification problems.")

        self.model = kwargs.pop('model', None)
        if self.model is None:
            raise TypeError(
                "__init__() missing required keyword-only argument: 'model'"
            )
        if not isinstance(self.model, ContinuousModel):
            raise TypeError(
                "model has to be a ContinuousModel or ProbabilisticModel"
            )

        self.model.train(self.dataset)

    def _get_scores(self, dvalue=None, retrain=True, *args, **kwargs):
        dataset = self.dataset
        if dvalue is None:
            if retrain:
                self.model.train(dataset, *args, **kwargs)
            unlabeled_entry_ids, X_pool = dataset.get_unlabeled_entries()
            dvalue = self.model.predict_real(X_pool)
        else:
            unlabled_entry_ids = dataset.get_unlabeled_idx()
            dvalue = self._check_dvalue(dvalue)
        
        # pclassidx = np.where( self.model.model.classes_ )[0][0]
        # trust interface would always put positive class at position 1
        score = dvalue[:, 1] 

        return unlabeled_entry_ids, score

    def make_query(self, n_ask=1, dvalue=None, return_score=False, retrain=False, *args, **kwargs):
        unlabeled_entry_ids, scores = self._get_scores(dvalue=dvalue, retrain=retrain, *args, **kwargs)
        
        ask_id = np.argsort(scores)[::-1][:n_ask]
        if n_ask == 1:
            ask_id = ask_id[0]

        if return_score:
            return unlabeled_entry_ids[ask_id], \
                   list(zip(unlabeled_entry_ids, scores))
        else:
            return unlabeled_entry_ids[ask_id]

     