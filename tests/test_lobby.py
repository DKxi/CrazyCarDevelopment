from pathlib import Path
import json, unittest
from streamlit.testing.v1 import AppTest


class LobbyTests(unittest.TestCase):
    def test_lobby_and_unlock_state(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state.highest_level_unlocked,1)
        self.assertEqual(app.session_state.control_mode,'keyboard')
        self.assertEqual(len([b for b in app.button if b.key and b.key.startswith('car_')]),7)
        app.session_state.highest_level_unlocked=12
        app.run()
        self.assertEqual(app.button(key='car_beasthunter').label,'Select BeastHunter')
        self.assertIn('View',app.button(key='car_nightfang').label)
        app.button(key='car_beasthunter').click().run()
        self.assertEqual(app.session_state.car_id,'beasthunter')
        self.assertEqual(app.session_state.highest_level_unlocked,12)


if __name__=='__main__':unittest.main()
