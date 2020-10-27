# Dbglordnikon

### Python Environment

Python: 3.7.1

### Setup

#### 1. Requirements
* pyenv ([Install](https://github.com/pyenv/pyenv))
* pyenv-virtualenv ([Install](https://github.com/pyenv/pyenv-virtualenv))
* SQLite3

#### 2. Setyp python environment
* Install python
  * `pyenv install 3.7.1`
* Create virtualenv
  * `pyenv virtualenv 3.7.1 dbglordnikon`
* If pyenv-virtualenv was not automatically activated
  * `pyenv activate dbglordnikon`

#### 3. Install Python dependencies
`pip install -r requirements.txt`

#### 4. bot.config
* Copy config and make appropriate changes
  * `cp bot.conf.example bot.conf`
  * `vim bot.conf`

#### 5. Run dbglordnikon
`python src/dbglordnikon.py`
