from modules.generate_summary import generate_summary

test_text = "The climate crisis is worsening every year as global temperatures continue to rise."
print(generate_summary(test_text, optimized=False))
print(generate_summary(test_text, optimized=True))
