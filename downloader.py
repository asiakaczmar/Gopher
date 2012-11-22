import pickle
import logging

import tweepy
from tweepy.error import TweepError
from tweepy import User

import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging

__author__ = "Joanna Kaczmar"
__all__ = ["TweeUser", "Downloader"]

class TweeUser(object):

    def __init__(self, user, friends_ids, followers_ids, tweets):
        self.user = user
        self.friends_ids = friends_ids
        self.followers_ids = followers_ids
        self.tweets = tweets

    @property
    def name(self):
        return self.user.screen_name


class Downloader(object):
        
    def __init__(self):
        self.api = self.get_connection()
        
    def get_connection(self):
        auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
        auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
        return tweepy.API(auth)
    
    def save(self, person, friends, followers):
        friends_ids = [f.id for f in friends]
        followers_ids = [f.id for f in followers]

        logger.debug('processing tweets')
        tweets = []
        for page in range(1, settings.TWEETS_PAGES):
            logger.debug('page %d' % page)
            t = person.timeline(page=page)
            if t:
                tweets += t
            else:
                break

        user = TweeUser(person, friends_ids, followers_ids, tweets)

        with open(settings.BASIC_PATH + 'user' + str(person.id) + '.txt', 'w') as f:
            pickle.dump(user, f)
            
    def load_connections(self):
        with open(settings.BASIC_PATH + 'connections.txt', 'r') as f:
            connections, new_connections = pickle.load(f)

            # dynamically adding a reference to my API instance (hacky;)
            for c in connections:
                c._api = self.api
            for nc in new_connections:
                nc._api = self.api

        return connections, new_connections

    def process_once(self, connections, new_connections):
        not_processed = list(connections)   # save a reference to what we need to process
        for c in connections:
            try:
                logger.debug('processing user %d' % c.id)
                # make sure we don't have too many friends :)
                friends = c.friends()[:settings.DEGREE]
                followers = c.followers()[:settings.DEGREE]
                logger.debug('got %d friends %d followers' % (len(friends), len(followers)))
                self.save(c, friends, followers)

                # add new friends&followers (remove duplicates)
                new_connections += friends
                new_connections += followers
                new_connections = list(set(new_connections))
                not_processed.pop(0)
            except TweepError, e:
                if e.reason != u'Not authorized':
                    with open(settings.BASIC_PATH + 'connections.txt', 'w') as f:
                        pickle.dump((not_processed, new_connections), f) # dump what was not processed
                    raise
        return new_connections

    def traverse(self, start_user=None):
        if start_user: 
            new_connections = [self.api.get_user(start_user)]
        else:
            logger.debug('loading connections')
            connections, new_connections = self.load_connections()
            new_connections = self.process_once(connections, new_connections)

        degrees_left = settings.DEPTH
        try:
            while degrees_left > 0:
                connections, new_connections = new_connections, []
                new_connections  = self.process_once(connections, new_connections)
                degrees_left -= 1
        except TweepError, e:
                logger.info('finishing traversing because of tweepy error:')
                logger.info(e.reason)

if __name__ == "__main__":
    d = Downloader()
    d.traverse()