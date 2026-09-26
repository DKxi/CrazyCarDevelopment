import math
import unittest
from game_config import LEVELS, CARS, SPONSORS, apply_progress, is_car_unlocked


def orient(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


class ConfigurationTests(unittest.TestCase):
    def test_levels_and_original_routes(self):
        self.assertEqual(len(LEVELS),23)
        self.assertEqual([t['number'] for t in LEVELS],list(range(1,24)))
        self.assertEqual([t['id'] for t in LEVELS],list(range(1,24)))
        self.assertEqual([t['name'] for t in LEVELS[:3]],['Daytona','Silverstone','Monaco'])
        self.assertEqual(LEVELS[0]['points'][0],[.18,.55])
        self.assertEqual(len({str(t['points']) for t in LEVELS}),23)

    def test_track_geometry(self):
        for track in LEVELS:
            with self.subTest(track=track['name']):
                points=track['points']
                self.assertGreaterEqual(len(points),2)
                self.assertNotEqual(points[0],points[-1])
                self.assertGreater(track['road_width'],26)
                self.assertGreater(track['time_limit'],0)
                self.assertGreater(math.hypot((points[0][0]-points[-1][0])*1000,(points[0][1]-points[-1][1])*650),track['road_width'])
                for x,y in points:
                    self.assertTrue(track['road_width']/2 < x*1000 < 1000-track['road_width']/2)
                    self.assertTrue(track['road_width']/2 < y*650 < 650-track['road_width']/2)
                for i,(a,b) in enumerate(zip(points,points[1:])):
                    self.assertNotEqual(a,b)
                    for c,d in zip(points[i+2:],points[i+3:]):
                        self.assertFalse(orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0,'Self intersection')

    def test_cars(self):
        self.assertEqual(len(CARS),7)
        for car in CARS.values():
            self.assertTrue({'name','color','accent','speed','handling','unlock_level'} <= car.keys())
        self.assertEqual(CARS['beasthunter']['name'],'BeastHunter')
        self.assertEqual(CARS['beasthunter']['unlock_level'],12)
        self.assertEqual(sorted(c['unlock_level'] for c in CARS.values()),[1,1,1,6,12,18,23])
        for key,car in CARS.items():
            self.assertTrue(is_car_unlocked(key,car['unlock_level']))
            self.assertFalse(is_car_unlocked(key,car['unlock_level']-1))

    def test_progress(self):
        highest=1
        for complete in range(1,len(LEVELS)+1):
            highest=apply_progress(highest,complete)
            self.assertEqual(highest,min(len(LEVELS),complete+1))
        self.assertEqual(apply_progress(12,1),12)
        for invalid in [None,True,-1,0,24,'12',12.5,{}]:
            self.assertEqual(apply_progress(1,invalid),1)
        self.assertEqual(apply_progress(1,12),1)

    def test_sponsors(self):
        self.assertEqual(len(SPONSORS),5)
        self.assertEqual(len({s['logo_path'] for s in SPONSORS.values()}),5)
        for sponsor in SPONSORS.values():
            self.assertTrue({'name','short_name','logo','logo_path'} <= sponsor.keys())
            self.assertIn('<svg',sponsor['logo'])


if __name__=='__main__':
    unittest.main()
