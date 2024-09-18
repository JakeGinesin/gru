import re

def gen_tighten_prompt_from_pbt_and_mutant(code : str, prop : str, mutant : str) -> str:
    prompt = f"""
You are provided with the following block of code, which is assumed to be the ground truth, a property-based test written using the Hypothesis python library, and a mutant of the code. The mutant was not killed by the property-based test during mutation testing. Please analyze why the property-based test failed to kill the mutant and improve the property-based test accordingly such that the mutant is killed. 

Ground-truth code:
```python
{code}
```

Property-Based Test:
```python
{prop}
```

Mutant code:
```python
{mutant}
```

First, explain why the mutant was not killed by the property-based test. Then, improve the property-based test to ensure that it can detect the mutant. Format your response as such:

(Explaination why the mutant was not killed)

```python
(your code)
```\n
"""
    return prompt

def gen_generalize_prompt_from_pbt_and_mutant(code : str, prop : str, mutant : str) -> str:
    prompt = f"""
You are provided with the following block of code, which is assumed to be the ground truth, a property-based test written using the Hypothesis python library, and a mutant of the code. The mutant was killed by the property-based test during mutation testing. Please analyze why the property-based test killed the mutant and change the property-based test such that the mutant is no longer killed. 

Ground-truth code:
```python
{code}
```

Property-Based Test:
```python
{prop}
```

Mutant code:
```python
{mutant}
```

First, explain why the mutant was killed by the property-based test. Then, change the property-based test to ensure it passes on the mutant. Format your response as such:

(Explaination why the mutant was killed)

```python
(your code)
```\n
"""
    return prompt

def extract_python_code(text: str) -> str:
    # Regular expression pattern to match Python code blocks
    pattern = r'```python\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return ""
