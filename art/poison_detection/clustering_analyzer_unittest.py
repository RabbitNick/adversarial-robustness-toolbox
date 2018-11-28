from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from art.poison_detection.size_analyzer import SizeAnalyzer
from art.poison_detection.relative_size_analyzer import RelativeSizeAnalyzer

logger = logging.getLogger('testLogger')


class TestActivationDefence(unittest.TestCase):

    # python -m unittest discover art/ -p 'clustering_analyzer_unittest.py'

    def test_size_analyzer(self):
        nb_clusters = 2
        nb_classes = 3
        clusters_by_class = [[[] for x in range(nb_clusters)] for y in range(nb_classes)]

        clusters_by_class[0] = [0, 1, 1, 1, 1]  # Class 0
        clusters_by_class[1] = [1, 0, 0, 0, 0]  # Class 1
        clusters_by_class[2] = [0, 0, 0, 0, 1]  # Class 2
        analyzer = SizeAnalyzer()
        assigned_clean_by_class, poison_clusters = analyzer.analyze_clusters(clusters_by_class)

        # print("clusters_by_class")
        # print(clusters_by_class)
        # print("assigned_clean_by_class")
        # print(assigned_clean_by_class)
        # print("poison_clusters")
        # print(poison_clusters)

        clean = 0
        poison = 1
        # For class 0, cluster 0 should be marked as poison.
        self.assertEqual(poison_clusters[0][0], poison)
        # For class 0, cluster 1 should be marked as clean.
        self.assertEqual(poison_clusters[0][1], clean)

        # Inverse relations for class 1
        self.assertEqual(poison_clusters[1][0], clean)
        self.assertEqual(poison_clusters[1][1], poison)

        self.assertEqual(poison_clusters[2][0], clean)
        self.assertEqual(poison_clusters[2][1], poison)

        poison = 0
        self.assertEqual(assigned_clean_by_class[0][0], poison)
        self.assertEqual(assigned_clean_by_class[1][0], poison)
        self.assertEqual(assigned_clean_by_class[2][4], poison)

    def test_size_analyzer_three(self):
        nb_clusters = 3
        nb_classes = 3
        clusters_by_class = [[[] for x in range(nb_clusters)] for y in range(nb_classes)]

        clusters_by_class[0] = [0, 1, 1, 2, 2]  # Class 0
        clusters_by_class[1] = [1, 0, 0, 2, 2]  # Class 1
        clusters_by_class[2] = [0, 0, 0, 2, 1, 1]  # Class 2
        analyzer = SizeAnalyzer()
        assigned_clean_by_class, poison_clusters = analyzer.analyze_clusters(clusters_by_class)

        # print("clusters_by_class")
        # print(clusters_by_class)
        # print("assigned_clean_by_class")
        # print(assigned_clean_by_class)
        # print("poison_clusters")
        # print(poison_clusters)

        clean = 0
        poison = 1
        # For class 0, cluster 0 should be marked as poison.
        self.assertEqual(poison_clusters[0][0], poison)
        # For class 0, cluster 1 and 2 should be marked as clean.
        self.assertEqual(poison_clusters[0][1], clean)
        self.assertEqual(poison_clusters[0][2], clean)

        self.assertEqual(poison_clusters[1][1], poison)
        self.assertEqual(poison_clusters[1][0], clean)
        self.assertEqual(poison_clusters[1][2], clean)

        self.assertEqual(poison_clusters[2][2], poison)
        self.assertEqual(poison_clusters[2][0], clean)
        self.assertEqual(poison_clusters[2][1], clean)

        poison = 0
        self.assertEqual(assigned_clean_by_class[0][0], poison)
        self.assertEqual(assigned_clean_by_class[1][0], poison)
        self.assertEqual(assigned_clean_by_class[2][3], poison)

    def test_relative_size_analyzer(self):
        nb_clusters = 2
        nb_classes = 4
        clusters_by_class = [[[] for x in range(nb_clusters)] for y in range(nb_classes)]

        clusters_by_class[0] = [0, 1, 1, 1, 1]  # Class 0
        clusters_by_class[1] = [1, 0, 0, 0, 0]  # Class 1
        clusters_by_class[2] = [0, 0, 0, 0, 1]  # Class 2
        clusters_by_class[3] = [0, 0, 1, 1, 1]  # Class 3
        analyzer = RelativeSizeAnalyzer()
        assigned_clean_by_class, poison_clusters = analyzer.analyze_clusters(clusters_by_class)

        # print("clusters_by_class")
        # print(clusters_by_class)
        # print("assigned_clean_by_class")
        # print(assigned_clean_by_class)
        # print("poison_clusters")
        # print(poison_clusters)

        clean = 0
        poison = 1
        # For class 0, cluster 0 should be marked as poison.
        self.assertEqual(poison_clusters[0][0], poison)
        # For class 0, cluster 1 should be marked as clean.
        self.assertEqual(poison_clusters[0][1], clean)

        # Inverse relations for class 1
        self.assertEqual(poison_clusters[1][0], clean)
        self.assertEqual(poison_clusters[1][1], poison)

        self.assertEqual(poison_clusters[2][0], clean)
        self.assertEqual(poison_clusters[2][1], poison)

        self.assertEqual(poison_clusters[3][0], clean)
        self.assertEqual(poison_clusters[3][1], clean)

        poison = 0
        self.assertEqual(assigned_clean_by_class[0][0], poison)
        self.assertEqual(assigned_clean_by_class[1][0], poison)
        self.assertEqual(assigned_clean_by_class[2][4], poison)
        self.assertEqual(sum(assigned_clean_by_class[3]), len(assigned_clean_by_class[3]))

    @unittest.expectedFailure
    def test_relative_size_analyzer_three(self):
        nb_clusters = 3
        nb_classes = 3
        clusters_by_class = [[[] for x in range(nb_clusters)] for y in range(nb_classes)]

        clusters_by_class[0] = [0, 1, 1, 2, 2]  # Class 0
        clusters_by_class[1] = [1, 0, 0, 2, 2]  # Class 1
        clusters_by_class[2] = [0, 0, 0, 2, 1, 1]  # Class 2
        analyzer = RelativeSizeAnalyzer()
        analyzer.analyze_clusters(clusters_by_class)

    if __name__ == '__main__':
        unittest.main()
