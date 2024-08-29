import yaml

class _Settings(dict):
    __slots__ = ()
    __getattr__ = dict.__getitem__
    # no __setattr__ for you!

try:
    settings_dict = yaml.safe_load(open('settings.yml'))
except FileNotFoundError:
    settings_dict = yaml.safe_load(open('irge/settings.yml'))

for k,v in settings_dict.items():
    settings_dict[k] = _Settings(v)



S = _Settings(settings_dict)




if __name__ == '__main__':
    print(f'{S=}')
    print(f'{S.program=}')
    print(f'{S.program.start_on_pause=}')
