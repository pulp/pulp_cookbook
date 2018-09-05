import asyncio

import asynctest

from pulp_cookbook.app.tasks.synchronizing import StageBase


class TestStageBase(asynctest.TestCase):

    async def test_none_only(self):
        in_q = asyncio.Queue()
        in_q.put_nowait(None)
        batch_it = StageBase.batches(in_q)
        with self.assertRaises(StopAsyncIteration):
            await batch_it.__anext__()

    async def test_single_batch_and_none(self):
        in_q = asyncio.Queue()
        in_q.put_nowait(1)
        in_q.put_nowait(2)
        in_q.put_nowait(None)
        batch_it = StageBase.batches(in_q)
        self.assertEqual([1, 2], await batch_it.__anext__())
        with self.assertRaises(StopAsyncIteration):
            await batch_it.__anext__()

    async def test_batch_and_single_none(self):
        in_q = asyncio.Queue()
        in_q.put_nowait(1)
        in_q.put_nowait(2)
        batch_it = StageBase.batches(in_q)
        self.assertEqual([1, 2], await batch_it.__anext__())
        in_q.put_nowait(None)
        with self.assertRaises(StopAsyncIteration):
            await batch_it.__anext__()

    async def test_two_batches(self):
        in_q = asyncio.Queue()
        in_q.put_nowait(1)
        in_q.put_nowait(2)
        batch_it = StageBase.batches(in_q)
        self.assertEqual([1, 2], await batch_it.__anext__())
        in_q.put_nowait(3)
        in_q.put_nowait(4)
        in_q.put_nowait(None)
        self.assertEqual([3, 4], await batch_it.__anext__())
        with self.assertRaises(StopAsyncIteration):
            await batch_it.__anext__()

    async def receiver(self, in_q, num):
        async for batch in StageBase.batches(in_q):
            self.assertEqual(len(batch), min(num, 2))
            num -= len(batch)
        self.assertEqual(num, 0)

    async def sender(self, out_q, num):
        for i in range(num):
            await StageBase.greedy_put(out_q, i)
        await out_q.put(None)

    async def test_greedy_put_batching(self):
        """Verify that greedy_put & batches create chunks with maximum queue length sizes"""
        for num in range(6):
            q = asyncio.Queue(maxsize=2)
            await asyncio.gather(self.receiver(q, num), self.sender(q, num))
