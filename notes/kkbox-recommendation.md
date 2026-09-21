The 11th ACM International Conference on Web Search and Data Mining (WSDM 2018) is challenging you to build a better music recommendation system using a donated dataset from KKBOX. WSDM (pronounced "wisdom") is one of the the premier conferences on web inspired research involving search and data mining. They're committed to publishing original, high quality papers and presentations, with an emphasis on practical but principled novel models.

Not many years ago, it was inconceivable that the same person would listen to the Beatles, Vivaldi, and Lady Gaga on their morning commute. But, the glory days of Radio DJs have passed, and musical gatekeepers have been replaced with personalizing algorithms and unlimited streaming services.

While the public’s now listening to all kinds of music, algorithms still struggle in key areas. Without enough historical data, how would an algorithm know if listeners will like a new song or a new artist? And, how would it know what songs to recommend brand new users?

WSDM has challenged the Kaggle ML community to help solve these problems and build a better music recommendation system. The dataset is from KKBOX, Asia’s leading music streaming service, holding the world’s most comprehensive Asia-Pop music library with over 30 million tracks. They currently use a collaborative filtering based algorithm with matrix factorization and word embedding in their recommendation system but believe new techniques could lead to better results.

Winners will present their findings at the conference February 6-8, 2018 in Los Angeles, CA. For more information on the conference, click here, and don't forget to check out the other KKBox/WSDM competition: KKBox Music Churn Prediction Challenge

Evaluation
Submissions are evaluated on area under the ROC curve between the predicted probability and the observed target.

Submission File
For each id in the test set, you must predict a probability for the target variable. The file should contain a header and have the following format:

id,target
2,0.3
5,0.1
6,1
etc.

data location: is in sandbox/data/kkbox

**user**: data is zipped. unzipp it and put in a dir if necessary. 
for initial EDA, sample a subset of the dataset is encouraged, if the data
set is large. You will want to EDA on all main data tables