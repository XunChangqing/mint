import lily.models.stressapp


def Main():
    with open('pattern.h', 'w') as f:
        for pd in lily.models.stressapp.PATTERN_ARRAY:
            f.write(f'uint32_t {pd.name}_data[] = {{')
            for d in pd.data:
                f.write(f'{d:#010x},')
            f.write(f'}};\n')

        f.write(f'pattern_data_t pattern_data_array[] = {{\n')
        for pd in lily.models.stressapp.PATTERN_ARRAY:
            f.write(f'{{.data = {pd.name}_data, .mask = {len(pd.data)-1:#x}}},\n')
        f.write(f'}};\n')

if __name__ == "__main__":
    Main()
