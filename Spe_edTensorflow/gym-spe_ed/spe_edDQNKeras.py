import gym
import numpy as np
import random
from keras.models import Sequential, load_model, Model
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, Input
from keras.optimizers import Adam
from keras import Input
from collections import deque
import os.path
import matplotlib.pyplot as plt
import copy

class DQN:
    def __init__(self, env):
        self.env     = env
        self.memory  = deque(maxlen=1000)
        
        self.gamma = 0.85
        self.epsilon = 1.0
        self.epsilon_min = 0.1 #0.01
        self.epsilon_decay = 0.9995
        self.learning_rate = 0.005
        self.tau = .125
        if os.path.exists('play.model.h5') and os.path.exists('target.model.h5'):
            self.model = load_model("play.model.h5")
            self.target_model = load_model('target.model.h5')
            print("Modelle geladen!")
        else:
            self.model = self.create_model()
            self.target_model = self.create_model()
        self.model.summary()

        self.loss_average = []
        self.loss_cont = []


    def create_model(self):
        model   = Sequential()
        state_shape  = self.env.observation_space.shape
        model.add(Input(state_shape))
        model.add(Flatten())
        model.add(Dense(256, activation="relu"))
        model.add(Dense(128, activation="relu"))
        model.add(Dense(self.env.action_space.n))
        model.compile(loss="mean_squared_error",
            optimizer=Adam(lr=self.learning_rate))
        return model

#gives back Random or predicted Action
    def act(self, state):
        self.epsilon *= self.epsilon_decay
        self.epsilon = max(self.epsilon_min, self.epsilon)
        if np.random.random() < self.epsilon:
            return (self.env.action_space.sample(), False)
        state = np.expand_dims(state, axis=0)
        return (np.argmax(self.model.predict(state)), True)

    def modelPrediction(self, state):
        state = np.expand_dims(state, axis=0)
        return np.argmax(self.model.predict(state))

#saves trajectory in memory
    def remember(self, state, action, reward, new_state, done, pred):
        self.memory.append([state, action, reward, new_state, done, pred])

    def replay(self):
        batch_size = 32
        if len(self.memory) < batch_size: 
            return

        samples = random.sample(self.memory, batch_size)
        for sample in samples:
            state, action, reward, new_state, done, pred = sample

            state = np.expand_dims(state, axis=0)

            target = self.target_model.predict(state)
            if done:
                target[0][action] = reward
            else:
                new_state = np.expand_dims(new_state, axis=0)
                Q_future = max(self.target_model.predict(new_state)[0])
                target[0][action] = reward + Q_future * self.gamma
            history = self.model.fit(state, target, epochs=1, verbose=0)

            if pred:
                self.loss_cont.append(history.history["loss"][0])
                if(len(self.loss_cont) >= 500):
                    avg = sum(self.loss_cont)/len(self.loss_cont)
                    self.loss_average.append(avg)
                    self.loss_cont.clear()
                    plt.plot(range(len(self.loss_average)), self.loss_average)
                    plt.title('model loss')
                    plt.ylabel('loss')
                    plt.xlabel('epoch')
                    plt.legend(['train', 'validation'], loc='upper left')
                    plt.savefig("loss_functiondrive.png")

    def target_train(self):
        weights = self.model.get_weights()
        target_weights = self.target_model.get_weights()
        for i in range(len(target_weights)):
            target_weights[i] = weights[i] * self.tau + target_weights[i] * (1 - self.tau)
        self.target_model.set_weights(target_weights)

    def save_model(self, fn, kindOfModel):
        path = F"{fn}" 
        if kindOfModel == "Model":
            self.model.save(path, save_format='h5')
            print("Model Saved!")
        elif kindOfModel == "Target":
            self.target_model.save(path, save_format="h5")
            print("Target Saved!")

def main():
    env     = gym.make("gym_spe_ed:spe_ed-v0")
    gamma   = 0.9
    epsilon = .95
    rew = 0
    steps  = 30000

    dqn_agent = DQN(env=env)
    average = []
    cur_state = env.reset()
    for step in range(steps):
        action_tuple = dqn_agent.act(cur_state)
        action = action_tuple[0]
        new_state, reward, done, _ = env.step(action)
        if np.random.random() > 0.90:
            dqn_agent.remember(cur_state, action, reward, new_state, done, action_tuple[1])
        elif len(np.nonzero(np.array(env.checkAllActions(copy.deepcopy(env.player), 0)))[0]) < 5:
            dqn_agent.remember(cur_state, action, reward, new_state, done, action_tuple[1])
        cur_state = new_state
        rew = rew + reward
        if done:
            cur_state = env.reset()
            print("{} Game Done with {} Rewards".format(step, rew))
            average.append(rew)
            rew = 0

        dqn_agent.replay()       # internally iterates default (prediction) model
        if step % 200 == 0:
            dqn_agent.target_train() # iterates target model

        if step % 500 == 0 and step != 0:
            print("Saved after {} Steps".format(step))
            dqn_agent.save_model("success.modelffa.h5", "Model")
            dqn_agent.save_model("target.modelffa.h5", "Target")
        
        if step % 100 == 0 and step != 0:
            rew = 0
            average_sum = sum(average)/len(average)
            average.clear()
            print("Last 200 Steps were completed with an average of {}".format(average_sum))
            cur_state = env.reset()
            done = False
            while not done:
                action = dqn_agent.modelPrediction(cur_state)  
                env.render()
                print("Aktion:", action)
                cur_state, reward, done, _ = env.step(action)
                rew += reward
            print("Score after {} Steps {}".format(step, rew))
            rew = 0
        
if __name__ == "__main__":
    main()
