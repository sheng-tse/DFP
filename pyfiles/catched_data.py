# import config

# print(
#     "Are you interested in any of the following occupation?\n",
#     "1. Software Engineer\n",
#     "2. Data Engineer\n",
#     "3. Data Scientist\n",
#     "4. Data Analyst\n",
#     "5. Machine Learning Engineer"
# )

# options = int(input(
#     "\nEnter an option by number to see job posts: "
# ))

# if options == 1:
#     se = config.pd.read_json("indeed_jobs_SE.json")
# elif options == 2:
#     de = config.pd.read_json("indeed_jobs_DE.json")
# elif options == 3:
#     ds = config.pd.read_json("indeed_jobs_DS.json")
# elif options == 4:
#     da = config.pd.read_json("indeed_jobs_DA.json")
# elif options == 5:
#     mle = config.pd.read_json("indeed_jobs_MLE.json")
# else:
#     print("\nIt was an invalid input. Please enter\n1 -> Software Engineer\n2 -> Data Engineer\n3 -> Data Scientist\n4 -> Data Analyst\n5 -> Machine Learning Engineer")
#     options = int(input(
#         "\nEnter an option by number to see job posts: "
#     ))

import json
import pandas as pd


def load_jobs(filename):
    """Load job data from JSON file."""
    try:
        return pd.read_json(filename)
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        return None


def show_jobs(df):
    """Display 5 job records at a time and allow navigation or full JD view."""
    total = len(df)
    index = 0

    while index < total:
        # Display 5 jobs
        for i in range(index, min(index + 5, total)):
            job = df.iloc[i]

            print(f"\n[{i+1}] {job.get('title', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")

            if 'salary' in job and pd.notna(job['salary']):
                print(f"Salary: {job['salary']}")

            # Preview of description
            desc = str(job.get('description', '')).strip().replace('\n', ' ')
            if len(desc) > 200:
                desc = desc[:200] + "..."
            print(f"Description: {desc}")
            print(f"URL: {job.get('url', 'N/A')}")
            print("-" * 80)

        index += 5

        # Navigation options
        while True:
            choice = input("\nOptions:\n"
                           "'n' = next 5 jobs\n"
                           "'m' = main menu\n"
                           "'q' = quit\n"
                           "'number' = view full JD for that job\n"
                           "Enter your choice: ").lower().strip()

            if choice == 'n':
                break  # show next 5
            elif choice == 'm':
                return  # back to main menu
            elif choice == 'q':
                exit()
            elif choice.isdigit():
                job_num = int(choice)
                if 1 <= job_num <= total:
                    job = df.iloc[job_num - 1]
                    print("\n" + "="*80)
                    print(f"FULL JOB DESCRIPTION: {job.get('title', 'N/A')}")
                    print(f"Company: {job.get('company', 'N/A')}")
                    print(f"Location: {job.get('location', 'N/A')}")
                    if 'salary' in job and pd.notna(job['salary']):
                        print(f"Salary: {job['salary']}")
                    print(f"URL: {job.get('url', 'N/A')}")
                    print("\nDescription:\n" + job.get('description', 'N/A'))
                    print("="*80)
                else:
                    print("Invalid job number.")
            else:
                print("Invalid input. Please try again.")

        if index >= total:
            print("\nNo more records.")
            input("Press Enter to return to main menu...")
            return


def main():
    while True:
        print("\nAre you interested in any of the following occupations?")
        print("1. Software Engineer")
        print("2. Data Engineer")
        print("3. Data Scientist")
        print("4. Data Analyst")
        print("5. Machine Learning Engineer")
        print("6. Quit")

        try:
            option = int(
                input("\nEnter an option by number to see job posts: "))
        except ValueError:
            print("Invalid input. Please enter a number 1–6.")
            continue

        file_map = {
            1: "indeed_jobs_SE.json",
            2: "indeed_jobs_DE.json",
            3: "indeed_jobs_DS.json",
            4: "indeed_jobs_DA.json",
            5: "indeed_jobs_MLE.json"
        }

        if option == 6:
            print("Goodbye!")
            break
        elif option in file_map:
            df = load_jobs(file_map[option])
            if df is not None:
                show_jobs(df)
        else:
            print("Please enter a valid option (1–6).")


if __name__ == "__main__":
    main()
