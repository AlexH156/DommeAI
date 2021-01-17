from gym.envs.registration import register

register(
    id='spe_ed-v0',
    entry_point='gym_spe_ed.envs:Spe_edEnv',
)