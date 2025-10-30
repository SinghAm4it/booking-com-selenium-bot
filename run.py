from BookingsBot.booking import Booking
import BookingsBot.constants as const

# This is a context manager and will automatically exit if the condition is satisfied
def main():
    print("\n=== Booking.com Interactive CLI ===\n")

    # Start browser session
    with Booking(teardown=False) as bot:
        bot.land_first_page()

        # Currency
        currency_change = input("Want to change currency of booking? (y/n) : ")
        if currency_change == "y":
            bot.change_currency(currency = input(f"Select Currency from {const.CURRENCIES}: "))

        # Location
        location = input("Enter destination location: ").strip()
        bot.search_location(location)

        # Date selection
        mode = input("Select mode ('calendar' or 'flexible'): ").strip().lower()

        if mode == "calendar":
            checkin = input("Enter check-in date (yyyy-mm-dd): ").strip()
            checkout = input("Enter checkout date (yyyy-mm-dd): ").strip()
            flexibility = input(f"Choose flexibility {const.DATE_FLEXIBILITY}: ").strip() or "Exact dates"

            bot.select_dates(mode="calendar",
                             checkin_date=checkin,
                             checkout_date=checkout,
                             flexibility=flexibility)

        elif mode == "flexible":
            stay_duration = input(f"Choose stay duration {const.STAY_DURATION}: ").strip()
            months = input("Enter months of stay (comma separated, e.g. Mar 2026,Apr 2026): ")
            time_of_stay = [m.strip() for m in months.split(",") if m.strip()]
            stay_duration_days = None
            day_number = None

            if stay_duration == "Other":
                stay_duration_days = int(input("Enter number of nights (1–90): "))
                day_number = int(input("Enter check-in day (1=Mon ... 7=Sun): "))

            bot.select_dates(mode="flexible",
                             stay_duration=stay_duration,
                             stay_duration_days=stay_duration_days,
                             day_number=day_number,
                             time_of_stay=time_of_stay)
        else:
            print("Invalid mode. Exiting.")
            return

        # Guests
        adults = int(input("Number of adults: "))
        children = int(input("Number of children: "))
        rooms = int(input("Number of rooms: "))
        pets = input("Travelling with pets? (y/n): ").lower() == "y"

        children_ages = []
        if children > 0:
            for i in range(children):
                age = int(input(f"Enter age for child {i+1} (0-17): "))
                children_ages.append(age)

        bot.select_guests(adults, children, rooms, pets, children_ages)

        # Perform search
        bot.search_results()

        # Optional price filter
        price_filter = input("Apply price range? (y/n): ").lower()
        if price_filter == "y":
            min_price = int(input("Enter min price: "))
            max_price = int(input("Enter max price: "))
            bot.set_price_slider(min_price, max_price)

        # Optional filters
        filters_choice = input("Apply property filters? (y/n): ").lower()
        if filters_choice == "y":
            print(f"Available filters:\n{', '.join(const.FILTERS[:10])} ...")  # show only few
            filters = input("Enter filters (comma separated): ").split(",")
            filters = [f.strip() for f in filters if f.strip()]
            bot.apply_filters(filters)

        # Sorting
        sort_choice = input(f"Sort the results? (y/n):").strip()
        if sort_choice == "y":
            sort_accordingto = input(f"Sort according to any of these \n {const.SORT_LIST}:").strip()
            bot.sort_according(sort_accordingto)

        # Extract & display results
        print("\n Extracting results...\n")
        results = bot.extract_results()
        print(results)

    print("\n Done! Browser remains open for manual inspection.\n")

if __name__ == "__main__":
    main()