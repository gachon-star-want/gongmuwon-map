import { useState } from 'react';
import { useDisclosure } from '@mantine/hooks';
import type { Place } from '../types';
import { submitClosureReport, submitTakedownRequest } from '../forms/reportFlows';

export interface ReportForm {
  category: string;
  reason: string;
  email: string;
}

interface UseReportFlowOptions {
  selectedPlace: Place | null;
  onAfterClosureReport?: () => Promise<void>;
  onAfterTakedownRequest?: (placeId: string) => void;
}

export function useReportFlow({ selectedPlace, onAfterClosureReport, onAfterTakedownRequest }: UseReportFlowOptions) {
  const [isTakedownModalOpen, takedown] = useDisclosure(false);
  const [isClosureModalOpen, closure] = useDisclosure(false);
  const [closureReason, setClosureReason] = useState<string | null>('방문해보니 폐업');
  const [reportForm, setReportForm] = useState<ReportForm>({ category: '식당 정보 오류', reason: '', email: '' });
  const [closureState, setClosureState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [requestState, setRequestState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [closureTurnstileToken, setClosureTurnstileToken] = useState<string | null>(null);
  const [requestTurnstileToken, setRequestTurnstileToken] = useState<string | null>(null);
  const [closureTurnstileReset, setClosureTurnstileReset] = useState(0);
  const [requestTurnstileReset, setRequestTurnstileReset] = useState(0);

  function setIsClosureModalOpen(open: boolean) {
    open ? closure.open() : closure.close();
  }

  function setIsTakedownModalOpen(open: boolean) {
    open ? takedown.open() : takedown.close();
  }

  async function submitClosureReportForm() {
    if (!selectedPlace) return;
    if (!closureTurnstileToken) {
      setClosureState('error');
      return;
    }
    setClosureState('submitting');
    try {
      await submitClosureReport({
        placeId: selectedPlace.id,
        note: closureReason ?? 'web-ui-report',
        turnstileToken: closureTurnstileToken,
      });
      setClosureState('done');
      setClosureTurnstileToken(null);
      await onAfterClosureReport?.();
    } catch {
      setClosureState('error');
      setClosureTurnstileToken(null);
      setClosureTurnstileReset((value) => value + 1);
    }
  }

  async function submitTakedownRequestForm() {
    if (!selectedPlace) return;
    if (!requestTurnstileToken) {
      setRequestState('error');
      return;
    }
    setRequestState('submitting');
    try {
      const email = reportForm.email.trim();
      await submitTakedownRequest({
        placeId: selectedPlace.id,
        reason: `${reportForm.category}: ${reportForm.reason.trim()}`,
        email,
        turnstileToken: requestTurnstileToken,
      });
      setRequestState('done');
      setRequestTurnstileToken(null);
      onAfterTakedownRequest?.(selectedPlace.id);
    } catch {
      setRequestState('error');
      setRequestTurnstileToken(null);
      setRequestTurnstileReset((value) => value + 1);
    }
  }

  function resetTakedownForm() {
    setReportForm({ category: '식당 정보 오류', reason: '', email: '' });
    setRequestState('idle');
    setRequestTurnstileToken(null);
    setRequestTurnstileReset((value) => value + 1);
  }

  function resetClosureForm() {
    setClosureReason('방문해보니 폐업');
    setClosureState('idle');
    setClosureTurnstileToken(null);
    setClosureTurnstileReset((value) => value + 1);
  }

  return {
    isClosureModalOpen,
    setIsClosureModalOpen,
    isTakedownModalOpen,
    setIsTakedownModalOpen,
    closureReason,
    setClosureReason,
    reportForm,
    setReportForm,
    closureState,
    requestState,
    closureTurnstileToken,
    setClosureTurnstileToken,
    requestTurnstileToken,
    setRequestTurnstileToken,
    closureTurnstileReset,
    requestTurnstileReset,
    submitClosureReport: submitClosureReportForm,
    submitTakedownRequestForm,
    resetTakedownForm,
    resetClosureForm,
  };
}
