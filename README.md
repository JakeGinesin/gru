# Gru: A Property-Based Test Refinement Tool
Gru is a toolset for systematically and concretely refining property-based tests (PBTs) implemented in [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) using mutation testing and large language models. It provides functionalities to tighten or generalize property-based tests  

![Gru lol](https://static.wikia.nocookie.net/despicableme/images/1/1c/Moonplan.png/revision/latest?cb=20130812133209)

## Installation

### Prereqs
- **Python 3.6 or higher**
- **OpenAI API Key** (required for LLM functionalities)

### Install via pip
- `pip install git+https://github.com/JakeGinesin/gru`

## OpenAI key
To use this project, set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage
Gru provides three main command-line tools:

1. `analyze-pbts`: Determines how effective the PBTs in your project are via mutation testing
2. `tighten-pbt`: Refines a PBT to make it stricter relative to the code, ensuring it is tighter to the code and kills *more* mutants
3. `generalize-pbt`: Refines a PBT to make it more general relative to the code, ensuring it accepts more behaviors and kills *less* mutants 

### Command-line tools
**tighten-pbt**

```bash
tighten-pbt <repo_dir> <pbt_name> [options]
```
- `<repo_dir>`: Path to your project's repository directory.
- `<pbt_name>`: Name of the property-based test function to refine.

Options:
- `--threshold`: (Optional) Threshold ratio of mutants that must be killed. Default is `0.8`.
- `--mutant_num`: (Optional) Number of mutants to generate. Default is `10`.
- `--max_iters`: (Optional) Maximum number of iterations for refinement. Default is `10`.

Example:
```bash
tighten-pbt /path/to/your/project test_my_property_based_function --threshold 0.9 --mutant_num 20
```

**generalize-pbt**

```bash
tighten-pbt <repo_dir> <pbt_name> [options]
```
- `<repo_dir>`: Path to your project's repository directory.
- `<pbt_name>`: Name of the property-based test function to refine.

Options:
- `--threshold`: (Optional) Threshold ratio of mutants that must remain unkilled. Default is `0.3`.
- `--mutant_num`: (Optional) Number of mutants to generate. Default is `10`.
- `--max_iters`: (Optional) Maximum number of iterations for refinement. Default is `10`.

Example:
```bash
generalize-pbt /path/to/your/project test_my_property_based_function --threshold 0.2 --mutant_num 15
```

**analyze-pbts**
```bash
analyze-pbts <repo_dir> [options]
```
- `<repo_dir>`: Path to your project's repository directory.

Options:
- `--mutant_num`: (Optional) Number of mutants to generate. Default is `10`.

Example:
```bash
analyze-pbts path/to/your/project test_my_property_based_function --mutant_num 15
```

### Using the API directly
You can also use the functions directly in code if you'd like. 

Example:
```
from gru.analyze_pbts import tighten_repo_pbt, generalize_repo_pbt

# Tighten a property-based test
result = tighten_repo_pbt(
    repo_dir='/path/to/your/project',
    pbt_name='test_my_property_based_function',
    threshhold=0.9,
    mutant_num=20,
    max_iters=10
)
print(result)

# Generalize a property-based test
result = generalize_repo_pbt(
    repo_dir='/path/to/your/project',
    pbt_name='test_my_property_based_function',
    threshhold=0.2,
    mutant_num=15,
    max_iters=10
)
print(result)
```

## Dependencies
Gru requires `openai`, `pytest`, `pytest-json-report`, and `hypothesis`. You can install these via `pip`:
```bash
pip install -r requirements.txt
```

## License
This project is licensed under the MIT license.

## Wishlist
This project is a research prototype and is under active development. Wishlist:
- [ ] analyze one PBT at a time
- [ ] implement the huggingface API as an alternative to openai
- [ ] an improved mutation engine that implements [e-graphs](https://effect.systems/doc/course-projects/cornelius.pdf), coverage-guided mutant generation, multithreading, and no source code modification (via only modifying `__pycache__`)
