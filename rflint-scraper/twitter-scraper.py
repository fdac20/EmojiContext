#!/usr/bin/env python3
# Author: Ryan Flint
#
# Description: This program uses the Tweepy python module to collect live twitter data based on a 
#	hardcoded keyword list (KEYWORDS) for a duration specified on the command-line in seconds. As 
#	tweets are collected, punctuation, "stop words", and user mentions are filtered out so that
#	the tweets can be analyzed in a word cloud. Additionally, for all tweets, the poster's username,
#	the local machine time of detection, and the timestamp associated with the tweet are collected.
#
#
#
# Synopsis: ./twitter-scraper.py [collection duration]
#######################################################################################################
from tweepy import Stream, OAuthHandler
from tweepy.streaming import StreamListener
from sys import stderr, exit, argv
from datetime import datetime

O_FILE = None;
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

#Tweets with only the below words will be searched for
KEYWORDS = ["😂", "❤️,", "😍", "🤣","😊", "🙏", "💕", "😭", "😘","👍", "😅", "👏", "😁", "♥️","🔥", "💔", "💖", "💙", "😢", "🤔", "😆", "🙄", "💪", "😉", "☺️ "];

#Giant list of stop words for filtering purposes
STOP_WORDS = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
"you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
"she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs',
'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is',
'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with',
'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now',
'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't",
'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn',
"needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"];

#List of punctuation
PUNCTUATION = ['.', ',', '!', '?', ';', ':', '-'];

class Listener(StreamListener):

	#Runs whenever a new tweet is detected
	#For this reason, this script might run for slightly longer than the specified duration due to the fact that tweets
	#aren't necessarily posted with the matching criteria at all times.
	def on_status(self, status):

		global O_FILE;

		#Figure out if we've surpassed the time limit
		#Turn the current time into seconds only for easy comparison
		now = datetime.now();
		now_seconds = (now.hour * 3600) + (now.minute * 60) + (now.second);

		#Collection done
		if ( (now_seconds - self.start_time) >= self.collection_duration ):
			print("Done.  (Duration: %d seconds)" % (now_seconds - self.start_time) );
			return False;
		
		#Figure out if this is a retweet or tweet and get the text of the tweet itself
		full_text = None;
		
		if ( hasattr(status, 'retweeted_status') ):
			rt = status.retweeted_status;
			try:
				full_text = rt.extended_tweet['full_text'];
			except:
				full_text = rt.text;

			full_text = "[RETWEET] " + full_text;

		else:
			#Not a retweet
			try:
				full_text = status.extended_tweet['full_text'];
			except:
				full_text = status.text;
		
		#Get rid of all the stop words, user mentions, and punctuation
		#filtered_text = filter_tweets(full_text);
		#Apparently python doesn't like the below logic in a function call...
		split_text = full_text.split();
		new_text = [];

		for word in split_text:

			#Knock out punctuation
			for p in PUNCTUATION:
				if (p in word):
					word = word.replace(p, "");

			if ( len(word) == 0):
				continue;

			#Eliminate user mentions and stop words
			if ( (word[0] != '@') and not (word.lower() in STOP_WORDS) ):
				new_text.append(word);

		full_text = " ".join(new_text);

		O_FILE.write("[TIME POSTED] %s\n" % format_date(datetime.now() ) );
		O_FILE.write("[TWITTER'S TIME POSTED] %s\n" % str(status.created_at) );
		O_FILE.write("[POSTER USER NAME] %s\n" % status.user.id);
		O_FILE.write(full_text);
		O_FILE.write("\n------------------------------------------------\n");
		return True;

	#If we are disconnected from Twitter for some reason, try to reconnect
	def on_error(self, status):
		if (status == 420):
			print("Too many requests sent in a short period of time. Disconnecting.,.", file=stderr);
		else:
			print("Error: %d" % status, file=stderr);

		print("Reconnecting and waiting...", file=stderr);
		print("Timestamp: %s" % format_date( datetime.now() ) );


		#Tell Tweepy to reconnect
		return True;

	#Constructor for the listener. Creates an output file for the streamed data
	def __init__(self, collection_duration):
		super(Listener, self).__init__();

		global O_FILE;

		self.collection_duration = collection_duration;

		try:
			O_FILE = open("collected-tweets.txt", mode = "w");
		except Exception as e:
			print("The following error occurred while trying to open/create the file: %s" % str(e), file=stderr);
			exit(1);

		#Log the start time so data collection can stop at the appropriate time
		now = datetime.now();
		self.start_time = (now.hour * 3600) + (now.minute * 60) + (now.second);

#Takes a datetime object and returns a date in the form "Month, Day, Year Hour:Minute:Second"
def format_date(d):
	return ("%s %s, %s %02d:%02d:%02d" % (MONTHS[d.month - 1], d.day, d.year, d.hour, d.minute, d.second) );
	

def main():

	#Check for the proper number of args
	if ( len(argv) < 2):
		print("usage: %s [collection duration in seconds]" % argv[0] );
		exit(1);

	collection_duration = None;
	
	try:
		collection_duration = int(argv[1]);

		if ( collection_duration <= 0):
			raise ValueError();
	except ValueError:
		print("The collection duration must be an integer greater than zero (0)", file=stderr);
		exit(1);

	# Since this file is going on github where "anyone" can see it, read developer keys and whatnot
	# from the secret file (which isn't going on github)
	secret_stuff_str = None;

	try:
		with open("secret.txt", "r") as f:
			secret_stuff_str = f.read();

	except Exception as e:
		print("The following error occurred trying to open the file: %s" % str(e) );
		exit(1);

	secret_stuff = secret_stuff_str.split();
	
	#Authenticate using keys/secrets given on twitter developer page
	consumer_key        = secret_stuff[0];
	consumer_secret     = secret_stuff[1];
	access_token_key    = secret_stuff[2];
	access_token_secret = secret_stuff[3];

	#Connect to Twitter
	auth = OAuthHandler(consumer_key, consumer_secret);
	auth.set_access_token(access_token_key, access_token_secret);

	print("Connected to Twitter. Searching entirety of Twitter for a period of %d seconds for keywords..." % collection_duration);

	#Initiate the stream
	#Extended mode because some tweets are truncated otherwise

	stream = Stream(auth, Listener(collection_duration), tweet_mode='extended' );

	#Start the stream. Search for English tweets only
	stream.filter( track=KEYWORDS, languages=['en']);

	O_FILE.close();
	print("Data collection finished. Results can be found in collected-tweets.txt");

if ( __name__ == '__main__'):
	main();
