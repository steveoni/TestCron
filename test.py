from dataflows import Flow, dump_to_path

data = [
  {'data': 'Hello'},
  {'data': 'World'}
]

def lowerData(row):
    row['data'] = row['data'].lower()
    

def lowerme(row):
    print(row)


if __name__ == "__main__":
    Flow(
        data,
        lowerData,
        dump_to_path("data3/test")
    ).process()
