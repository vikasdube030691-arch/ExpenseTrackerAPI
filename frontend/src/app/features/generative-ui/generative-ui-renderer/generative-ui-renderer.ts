import { NgComponentOutlet } from '@angular/common';
import { Component, Type, computed, input } from '@angular/core';

import { resolveComponent } from '../component-registry';
import { UIComponent } from '../models/ui-component.model';
import { validateUiBlocks } from '../ui-component-validator';
import { UnknownFallback } from '../components/unknown-fallback/unknown-fallback';

interface RenderableBlock {
  readonly key: string;
  readonly component: Type<unknown>;
  readonly data: UIComponent;
}

/**
 * The single entry point from "untrusted AI output" to rendered Angular
 * components. Pass whatever came back on the wire (e.g. a chat message's
 * `metadata['ui_blocks']`) as `payload` — it is typed `unknown` on purpose,
 * because that is exactly the trust level this data has, regardless of
 * whether the backend already validated it.
 *
 * Pipeline: `payload` (untrusted JSON)
 *   → `validateUiBlocks` (Generative UI schema, a client-side mirror of
 *     `app/schemas/generative_ui.py`)
 *   → `resolveComponent` (Component Registry)
 *   → `NgComponentOutlet` (Dynamic Component Rendering).
 *
 * A block that fails validation (unknown component name, unknown prop, HTML
 * in text, an action outside the whitelist, ...) never reaches
 * `NgComponentOutlet` at all. It isn't silently dropped either: `unsafeCount`
 * surfaces how many blocks were rejected so the template can show one
 * `UnknownFallback` notice, instead of either crashing the message or making
 * filtered content disappear without a trace.
 */
@Component({
  selector: 'app-generative-ui-renderer',
  imports: [NgComponentOutlet, UnknownFallback],
  templateUrl: './generative-ui-renderer.html',
  styleUrl: './generative-ui-renderer.scss'
})
export class GenerativeUiRenderer {
  readonly payload = input<unknown>(null);

  private readonly validation = computed(() => validateUiBlocks(this.payload()));

  protected readonly blocks = computed<readonly RenderableBlock[]>(() =>
    this.validation().blocks.map((data, index) => ({
      key: `${data.component}-${index}`,
      component: resolveComponent(data.component),
      data
    }))
  );

  protected readonly unsafeCount = computed(() => this.validation().rejected.length);

  protected readonly fallbackReason = computed(() => {
    const count = this.unsafeCount();
    return count === 1
      ? '1 item in this response could not be safely displayed and was hidden.'
      : `${count} items in this response could not be safely displayed and were hidden.`;
  });
}
