goal: predict customer churn.
data is /Users/alex/dev/sandbox/data/playground-series-churn
test data we don't have ground truth. that's for kaggle submission
split train and train validation and test and evaluat on that test set

official output requirement:
Evaluation
The evaluation section describes how submissions will be scored and how participants should format their submissions. You don't need a sub-title at the top; the page title appears above. Below is an example of a typical evaluation page.

Submissions are evaluated on area under the ROC curve between the predicted probability and the observed target.

Submission File
For each id in the test set, you must predict a probability for the Churn variable. The file should contain a header and have the following format:

id,Churn
594194,0.1
594195,0.3
594196,0.2
etc.