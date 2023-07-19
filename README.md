# Warren Chatbot v0.0.2

Warren is a chatbot for investment clubs to analyze stocks, report on club fundamentals and more.

[![linting: flake8](https://img.shields.io/badge/linting-flake8-yellowgreen)](https://flake8.pycqa.org/en/latest/)

## Getting Started

TO build a development version of this software, refer to the [CONTRIBUTING.md](./CONTRIBUTING.md) file for development
instructions.

## Folder Structure
```
.
├-- .github                                 # Github Actions folder
├-- src/                                
|   └-- warrenBot/                          # main module for application
|       ├-- resources/
|       ├-- tests/                          # unit tests        
|       ├-- __init__.py                     # module init
|       ├-- alphavantage.py                 # module for alphavantage transactions
|       ├-- analysis.py                     # module for quant analysis methods
|       ├-- portfolio_analysis.py           # module for portfolio analysis function
|       ├-- stock_analysis.py               # module for stock analysis function
|       └-- utilites.py                     # module for general utility functions
├-- .bumpversion.cfg                        # bumpversion configuration for version incrementation
├-- .gitignore                              # Typical gitignore file
├-- bot_config.template.info                # INI template for bot_config (remove .template for function)
├-- CHANGELOG.md                            # running record (human readable) of version changes
├-- club_info_template.json                 # JSON template for club/portfolio info
├-- club_stocks.csv                         # CSV template for club/portfolio buy and sell of stocks
├-- CONTRIBUTING.md                         # Directions and standards for contributing to this application
├-- dchat.py                                # Discord chatbot entrypoint
├-- humans.txt                              # Running list of all contributors
├-- LICENSE                                 # Source of truth for required LICENSE
├-- pyproject.toml                          # Python toml setup configurations
├-- README.md                               # This file
├-- requirements.txt                        # Basic pip requirements file
├-- setup.py                                # Backwards compatable python setup script
├-- stocks.pkl                              # Pickle file of latest stocks download (prevent extra calls to 
|                                           # apvantage API)
└-- tox.ini                                 # configuration file for testing via tox
```

## Deployment

## Built With

* [Python3.11](https://www.python.org/downloads/release/python-3110/)
* [Bump2Version](https://github.com/c4urself/bump2version)
* [Pandas](https://pandas.pydata.org/)
* [NumPy](https://numpy.org/)
* [PrettyTables](https://github.com/jazzband/prettytable)
* [requests](https://docs.python-requests.org/en/latest/index.html)
* [matplotlib](https://matplotlib.org/)
* [mplfinance](https://github.com/matplotlib/mplfinance)

## Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct, installing, developing, and the 
process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the 
[tags on this repository](https://gitlab.com/dunns-valve-testers/report_generator/-/tags). 

## Authors

See the list of [contributors](./humans.txt) who participated in this project.

## License

This project uses libraries and software listed in the [Built With](README.md#built-with) section. See the 
[LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

* [Lance James](https://github.com/lancejames221b) and his Hal DiscordBot for the idea and initial structure.
