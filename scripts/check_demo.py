from search_mesc import search

result = search("لوله دو اینچی پلاستیکی برند داچ", 10)
assert len(result["results"]) == 10
assert all(item["manufacturer"] == "Dutch" for item in result["results"])
assert all(item["size_inch"] == 2 for item in result["results"])
assert all(item["synthetic"] for item in result["results"])
print("demo search check passed")
