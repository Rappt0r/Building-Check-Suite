This program is a **building inspection app** created using the **Kivy framework** for a graphical user interface. Here's what it does in simple terms:

1. **Start or Resume an Inspection**  
   - Users can start a **new building check** or **resume** a previously saved one.

2. **Floor and Room Selection**  
   - The app loads data from a `floors.json` file to display a list of floors and their rooms.  
   - Users select a **floor** and then a **room** to inspect.

3. **Checking Items in a Room**  
   - Each room contains specific items to check (e.g., doors, lights, fire extinguishers).  
   - Users can mark items as **"OK"** or **"Issue"** and add **notes** if needed.

4. **Saving and Loading Data**  
   - The app **saves** the inspection progress into a CSV file.  
   - If the app is reopened, it can **load** the last saved inspection and continue from where it left off.

5. **User Interface**  
   - It uses buttons, labels, and pop-ups to interact with the user.  
   - There is navigation to go back or return to the home screen.
