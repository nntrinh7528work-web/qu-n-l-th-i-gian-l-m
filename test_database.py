# -*- coding: utf-8 -*-
import unittest
import os
import sqlite3
from datetime import date
from unittest.mock import patch # Import patch

import database
import db_wrapper
import calculations

# Override DB path for testing
TEST_DB_PATH = "test_work_hours.db"
database.DEFAULT_DB_PATH = os.path.abspath(TEST_DB_PATH)
database.DB_PATH = database.DEFAULT_DB_PATH

class TestWorkHoursApp(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh database before each test."""
        # Clean up if exists
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass
                
        database.init_database()
        
        # Add a default job for testing
        self.job_id = database.add_job("Test Job", 1000.0)

    def tearDown(self):
        """Clean up after tests."""
        # Close any lingering connections if possible, though functions open/close on demand
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass

    def test_add_shift(self):
        """Test adding a new work shift."""
        shift_id = database.add_shift(
            work_date=date(2023, 1, 1),
            job_id=self.job_id,
            start_time="09:00",
            end_time="17:00",
            break_hours=1.0,
            total_hours=7.0
        )
        self.assertIsNotNone(shift_id)
        self.assertGreater(shift_id, 0)
        
        # Verify it exists
        shift = database.get_shift_by_id(shift_id)
        self.assertIsNotNone(shift)
        self.assertEqual(shift['total_hours'], 7.0)

    def test_add_shift_invalid_job(self):
        """Test adding shift with non-existent job ID."""
        shift_id = database.add_shift(
            work_date=date(2023, 1, 1),
            job_id=9999, # Invalid ID
            start_time="09:00",
            end_time="17:00",
            break_hours=1.0,
            total_hours=7.0
        )
        self.assertIsNone(shift_id)

    def test_update_shift(self):
        """Test updating a shift."""
        shift_id = database.add_shift(
            work_date=date(2023, 1, 1),
            job_id=self.job_id,
            start_time="09:00",
            end_time="17:00",
            break_hours=1.0,
            total_hours=7.0
        )
        
        success = database.update_shift(
            shift_id, 
            shift_name="Updated Shift",
            total_hours=8.0
        )
        self.assertTrue(success)
        
        shift = database.get_shift_by_id(shift_id)
        self.assertEqual(shift['shift_name'], "Updated Shift")
        self.assertEqual(shift['total_hours'], 8.0)

    def test_delete_shift(self):
        """Test deleting a shift."""
        shift_id = database.add_shift(
            work_date=date(2023, 1, 1),
            job_id=self.job_id,
            start_time="09:00",
            end_time="17:00",
            break_hours=1.0,
            total_hours=7.0
        )
        
        success = database.delete_shift(shift_id)
        self.assertTrue(success)
        
        shift = database.get_shift_by_id(shift_id)
        self.assertIsNone(shift)

    def test_calculations_overnight(self):
        """Test overnight calculation logic."""
        # 22:00 to 06:00 (Next day) -> 8 hours - 1h break = 7h
        hours, error = calculations.calculate_work_hours("22:00", "06:00", 1.0)
        self.assertEqual(hours, 7.0)
        self.assertEqual(error, "")

    def test_calculations_24_hours(self):
        """Test 24 hours edge case."""
        # 22:00 to 22:00 -> 24 hours - 1h break = 23h
        hours, error = calculations.calculate_work_hours("22:00", "22:00", 1.0)
        self.assertEqual(hours, 23.0)
        self.assertEqual(error, "")

    def test_get_shifts_by_range(self):
        """Test fetching shifts by range."""
        database.add_shift(date(2023, 1, 1), self.job_id, "08:00", "12:00", 0, 4.0)
        database.add_shift(date(2023, 1, 2), self.job_id, "08:00", "12:00", 0, 4.0)
        database.add_shift(date(2023, 1, 5), self.job_id, "08:00", "12:00", 0, 4.0)
        
        shifts = database.get_shifts_by_range(date(2023, 1, 1), date(2023, 1, 3))
        self.assertEqual(len(shifts), 2)

    def test_db_wrapper_compatibility(self):
        """Test wrapper functions with explicit SQLite mode."""
        # Force _check_supabase to False
        with patch('db_wrapper._check_supabase', return_value=False):
            shift_id = db_wrapper.add_shift(
                work_date=date(2023, 1, 1),
                job_id=self.job_id,
                start_time="09:00",
                end_time="17:00",
                break_hours=1.0,
                total_hours=7.0
            )
            self.assertIsNotNone(shift_id, "db_wrapper.add_shift returned None")
            self.assertNotEqual(shift_id, -1)

if __name__ == '__main__':
    unittest.main()
