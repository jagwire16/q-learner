import argparse
import logging
import pickle
import random
import sys
from collections import defaultdict

import numpy as np

import gym
from gym import wrappers


class QFunc:
    """
    Q-Learner
    gamma_factor -  discount coef
    (1 - epsilon) - exploration probability
    exploration_decay - exploration decay on each action
    q_table - history of observed states  nested hashtable state => action => reward
    """

    learning_rate = 0.1
    gamma_factor = 0.9
    epsilon = 0.4
    exploration_decay = 1.00005

    q_hits = 0
    all_hits = 1

    def __init__(self, action_space):
        self.action_space = action_space
        self.q_table = defaultdict(dict)

    def _hash_word_state(self, state: np.array) -> int:
        """
        Hashes word state of multy dim np.array into an int. Will result a low memory footprint for
        hash table
        """
        return hash(tuple(reduce_word(state).flatten()))

    def size(self) -> int:
        return len(self.q_table)

    def learn(self,
              old_state: np.array,
              action: int,
              reward: int,
              new_state: np.array) -> None:
        """
        Definition of Q-learning taken from

        https://en.wikipedia.org/wiki/Q-learning
        """
        q_old_state = self.q_table[self._hash_word_state(old_state)].get(
            action, 0)  # use random to init table if value does not exists
        q_new_state_max = max(self.q_table[self._hash_word_state(new_state)] or
                              [0])
        self.q_table[self._hash_word_state(old_state)][action] = q_old_state + self.learning_rate * \
            (reward + self.gamma_factor * (q_new_state_max - q_old_state))

    def make_decision(self, state: np.array) -> None:
        """
        Decides which action to take.

        Args:
         	state: current board state
        """

        self.epsilon = self.exploration_decay * self.epsilon
        if random.random() > self.epsilon:
            return self.action_space.sample()
        else:
            if self.q_table[self._hash_word_state(state)]:
                self.q_hits += 1
            self.all_hits += 1
            action = max(self.q_table[self._hash_word_state(state)] or
                         [self.action_space.sample()])
            return action

    def hit_ration(self) -> float:
        return self.q_hits / self.all_hits

    def exploration_factor(self) -> float:
        return min((1 - self.epsilon) * 100, 100)


def reduce_word(data, rows=60, cols=120):
    data = data.reshape([210, 160 * 3])
    row_sp = data.shape[0] // rows
    col_sp = data.shape[1] // cols
    tmp = np.sum(data[i::row_sp] for i in range(row_sp))
    return np.sum(tmp[:, i::col_sp] for i in range(col_sp))


def train():
    env = gym.make('SpaceInvaders-v0')
    outdir = '/tmp/q-space-func'
    # env = wrappers.Monitor(env, directory=outdir, force=True)
    env.seed(0)
    q_learner = QFunc(env.action_space)
    episode_count = 1000
    reward = 0
    done = False
    max_score = 0
    all_time_max = 0
    for i in range(episode_count):
        state = env.reset()
        print('#' * 50)
        print("Current score", max_score)
        print("Max score", all_time_max)
        print("Game number #", i)
        print("Observed states", q_learner.size())
        print("Exploration probability {:.1f}%".format(
            q_learner.exploration_factor()))
        print("Qs memory hit", q_learner.hit_ration())
        all_time_max = max(all_time_max, max_score)
        max_score = 0
        lives = 3
        while True:
            action = q_learner.make_decision(state)
            state_ = state
            state, reward, done, info = env.step(action)
            penalty = 0
            new_lives = info['ale.lives']
            if new_lives < lives:
                lives = new_lives
                penalty = 10
            q_reward = (reward if not done else -1) - penalty
            q_learner.learn(
                old_state=state_,
                action=action,
                reward=q_reward,
                new_state=state)
            max_score += reward
            if done:
                break
            if q_learner.epsilon > 0.5:
                env.render()
    with open('qfunc.pickle', 'wb') as handle:
        pickle.dump(q_learner, handle, protocol=pickle.HIGHEST_PROTOCOL)
    env.close()


if __name__ == '__main__':
    train()
