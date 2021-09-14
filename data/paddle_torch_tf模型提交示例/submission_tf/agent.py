import os
import numpy as np
from tensorflow.keras import models, layers


def wrap_action(adjust_gen_p):
    act = {
        'adjust_gen_p': adjust_gen_p,
        'adjust_gen_v': np.zeros_like(adjust_gen_p)
    }
    return act

OBS_DIM = 620
ACT_DIM = 54


class Agent(object):

    def __init__(self, settings, this_directory_path):
        self.settings = settings
        
        model_path = os.path.join(this_directory_path, "saved_model/model.h5")

        self.model = models.Sequential([
            layers.Dense(100, input_dim=OBS_DIM, activation='relu'),
            layers.Dense(ACT_DIM, activation="softmax")
        ])

        
        #self.model.save(model_path)
        self.model = models.load_model(model_path)

        
    def act(self, obs, reward, done=False):
        features = self._process_obs(obs)
        features = np.expand_dims(features, 0)
        action = self.model.predict(features)[0]
        ret_action = self._process_action(obs, action)
        return ret_action
    

    def _process_obs(self, obs):
        # loads
        loads = []
        loads.append(obs.load_p)
        loads.append(obs.load_q)
        loads.append(obs.load_v)
        loads = np.concatenate(loads)

        # prods
        prods = []
        prods.append(obs.gen_p)
        prods.append(obs.gen_q)
        prods.append(obs.gen_v)
        prods = np.concatenate(prods)
        
        # rho
        rho = np.array(obs.rho) - 1.0
        
        features = np.concatenate([loads, prods, rho.tolist()])
        return features
    
    def _process_action(self, obs, action):
        N = len(action)

        gen_p_action_space = obs.action_space['adjust_gen_p']

        low_bound = gen_p_action_space.low
        high_bound = gen_p_action_space.high

        mapped_action = low_bound + (action - (-1.0)) * (
            (high_bound - low_bound) / 2.0)
        mapped_action[self.settings.balanced_id] = 0.0
        mapped_action = np.clip(mapped_action, low_bound, high_bound)
        
        return wrap_action(mapped_action)
