#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "Presets.h"

class PresetManager : private juce::ValueTree::Listener
{
public:
    PresetManager (juce::AudioProcessorValueTreeState& vts)
        : apvts (vts), defaultState (vts.copyState())
    {
        reattachListener();
        scanUserPresets();
    }

    ~PresetManager() override
    {
        if (listenedState.isValid())
            listenedState.removeListener (this);
    }

    // ── Counts ──────────────────────────────────────────────────

    int getNumFactoryPresets() const
    {
        int c = 0;
        getFactoryPresetList (c);
        return c;
    }

    int getNumUserPresets() const { return userPresets.size(); }
    int getNumPresets() const     { return getNumFactoryPresets() + getNumUserPresets(); }

    // ── Naming ──────────────────────────────────────────────────

    juce::String getPresetName (int index) const
    {
        int nFactory = getNumFactoryPresets();
        if (index >= 0 && index < nFactory)
        {
            int c = 0;
            auto* list = getFactoryPresetList (c);
            return list[index].name;
        }
        int ui = index - nFactory;
        if (ui >= 0 && ui < userPresets.size())
            return userPresets[ui].name;
        return {};
    }

    bool isFactory (int index) const { return index >= 0 && index < getNumFactoryPresets(); }

    // ── Load ────────────────────────────────────────────────────

    void loadPreset (int index)
    {
        int nFactory = getNumFactoryPresets();
        bool loaded = false;

        if (index >= 0 && index < nFactory)
        {
            loaded = loadFactoryPreset (index);
        }
        else
        {
            int ui = index - nFactory;
            if (ui >= 0 && ui < userPresets.size())
                loaded = loadUserFile (userPresets[ui].file);
        }

        if (! loaded)
            return;

        currentIndex = index;
        dirty = false;
    }

    // ── Init (reset all params to defaults) ─────────────────────

    void initPreset()
    {
        loading = true;
        apvts.replaceState (defaultState.createCopy());
        reattachListener();
        loading = false;
        currentIndex = -1;
        dirty = false;
    }

    /** Re-subscribe to the (potentially new) ValueTree after replaceState(). */
    void reattachListener()
    {
        if (listenedState.isValid())
            listenedState.removeListener (this);

        listenedState = apvts.state;
        if (listenedState.isValid())
            listenedState.addListener (this);
    }

    // ── Save user preset ────────────────────────────────────────

    bool userPresetExists (const juce::String& name) const
    {
        auto safeName = toSafeFilename (name);
        if (safeName.isEmpty()) return false;
        return getPresetDirectory().getChildFile (safeName + ".tsukipreset").existsAsFile();
    }

    bool saveUserPreset (const juce::String& name, bool allowOverwrite = false)
    {
        auto dir = getPresetDirectory();
        if (! dir.isDirectory())
            return false;

        auto safeName = toSafeFilename (name);
        if (safeName.isEmpty())
            return false;

        auto file = dir.getChildFile (safeName + ".tsukipreset");
        if (file.existsAsFile() && ! allowOverwrite)
            return false;

        auto state = apvts.copyState();
        auto stateXml = state.createXml();
        if (stateXml == nullptr)
            return false;

        juce::XmlElement root ("TsukiSynthPreset");
        root.setAttribute ("name", name);
        root.setAttribute ("version", 1);
        root.addChildElement (stateXml.release());

        if (! root.writeTo (file))
            return false;

        scanUserPresets();

        int nFactory = getNumFactoryPresets();
        for (int i = 0; i < userPresets.size(); ++i)
        {
            if (userPresets[i].name == name)
            {
                currentIndex = nFactory + i;
                break;
            }
        }
        dirty = false;
        return true;
    }

    // ── Delete user preset ──────────────────────────────────────

    bool deleteUserPreset (int index)
    {
        int ui = index - getNumFactoryPresets();
        if (ui < 0 || ui >= userPresets.size())
            return false;

        userPresets[ui].file.deleteFile();
        scanUserPresets();

        if (currentIndex == index)
        {
            currentIndex = 0;
            dirty = false;
        }
        return true;
    }

    // ── State ───────────────────────────────────────────────────

    int  getCurrentIndex() const { return currentIndex; }
    bool isDirty()         const { return dirty; }

    void setCurrentIndex (int i)
    {
        currentIndex = juce::jlimit (-1, getNumPresets() - 1, i);
        dirty = false;
    }

    // ── Scan disk ───────────────────────────────────────────────

    void scanUserPresets()
    {
        userPresets.clear();
        auto dir = getPresetDirectory();

        for (const auto& entry :
             juce::RangedDirectoryIterator (dir, false, "*.tsukipreset",
                                            juce::File::findFiles))
        {
            auto file = entry.getFile();
            auto xml  = juce::XmlDocument::parse (file);
            if (xml == nullptr)
                continue;

            juce::String name = xml->getStringAttribute ("name",
                                    file.getFileNameWithoutExtension());
            userPresets.add ({ name, file });
        }

        struct NameCmp
        {
            int compareElements (const UserPreset& a, const UserPreset& b) const
            {
                return a.name.compareIgnoreCase (b.name);
            }
        };
        NameCmp cmp;
        userPresets.sort (cmp);
    }

private:
    struct UserPreset
    {
        juce::String name;
        juce::File   file;
    };

    juce::AudioProcessorValueTreeState& apvts;
    juce::ValueTree defaultState;
    juce::ValueTree listenedState;
    juce::Array<UserPreset> userPresets;
    int  currentIndex = -1;
    std::atomic<bool> dirty   { false };
    std::atomic<bool> loading { false };

    // ── ValueTree::Listener ─────────────────────────────────────

    void valueTreePropertyChanged (juce::ValueTree&, const juce::Identifier&) override
    {
        if (! loading)
            dirty = true;
    }

    void valueTreeChildAdded        (juce::ValueTree&, juce::ValueTree&)                  override {}
    void valueTreeChildRemoved      (juce::ValueTree&, juce::ValueTree&, int)             override {}
    void valueTreeChildOrderChanged  (juce::ValueTree&, int, int)                         override {}
    void valueTreeParentChanged      (juce::ValueTree&)                                   override {}

    // ── Factory preset loader ───────────────────────────────────

    bool loadFactoryPreset (int index)
    {
        int count = 0;
        auto* presets = getFactoryPresetList (count);
        if (index < 0 || index >= count)
            return false;

        loading = true;
        apvts.replaceState (defaultState.createCopy());
        reattachListener();

        const auto& preset = presets[index];
        for (int i = 0; i < preset.numParams; ++i)
        {
            const auto& entry = preset.params[i];
            if (auto* param = apvts.getParameter (entry.paramID))
            {
                float normalized = param->convertTo0to1 (entry.rawValue);
                param->setValueNotifyingHost (normalized);
            }
        }
        loading = false;
        return true;
    }

    // ── User preset file loader ─────────────────────────────────

    bool loadUserFile (const juce::File& file)
    {
        auto xml = juce::XmlDocument::parse (file);
        if (xml == nullptr)
            return false;

        auto* paramsXml = xml->getChildByName (apvts.state.getType());
        if (paramsXml == nullptr)
            return false;

        loading = true;
        apvts.replaceState (juce::ValueTree::fromXml (*paramsXml));
        reattachListener();
        loading = false;
        return true;
    }

    // ── Helpers ─────────────────────────────────────────────────

    juce::File getPresetDirectory() const
    {
        auto dir = juce::File::getSpecialLocation (
                       juce::File::userApplicationDataDirectory)
                       .getChildFile ("TsukiSynth")
                       .getChildFile ("Presets");
        dir.createDirectory();
        return dir;
    }

    static juce::String toSafeFilename (const juce::String& name)
    {
        return name.removeCharacters ("/\\:*?\"<>|")
                   .trim()
                   .substring (0, 64);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PresetManager)
};
